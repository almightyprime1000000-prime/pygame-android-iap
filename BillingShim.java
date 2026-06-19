// ============================================================
// BillingShim.java
// Author: Wonder Kofi Junior (Almighty Prime)
// Project: Skiptrace (com.almightyprime.skiptrace)
//
// PURPOSE:
//   This Java class wraps the Google Play Billing Library so it
//   can be used from Python via Pyjnius in a Pygame Android game.
//
// WHY THIS EXISTS:
//   The Google Play Billing Library is Java-based and uses complex
//   asynchronous callbacks. Pyjnius (the Python-Java bridge) cannot
//   reliably implement all of its listener interfaces directly in Python.
//
//   The solution: implement all the billing logic in Java, and expose
//   a simple event queue (pollEvent()) that Python can check each frame.
//   This avoids threading issues and keeps the Python side simple.
//
// HOW TO USE:
//   1. Place this file in your Android project's Java source folder:
//      <project>/src/main/java/com/almightyprime/skiptrace/
//   2. Add the Google Play Billing dependency to your build.gradle:
//      implementation 'com.android.billingclient:billing:6.x.x'
//   3. Use iap.py on the Python side — it handles all interaction
//      with this class automatically.
//
// EVENT QUEUE:
//   All results are pushed as strings into a ConcurrentLinkedQueue.
//   Python calls pollEvent() to read one event at a time.
//   Possible events: "ready", "init_failed", "disconnected",
//                    "purchased:<productId>", "not_found:<productId>",
//                    "failed", "not_ready"
// ============================================================

package com.almightyprime.skiptrace;

import android.app.Activity;
import com.android.billingclient.api.*;
import java.util.List;
import java.util.concurrent.ConcurrentLinkedQueue;

public class BillingShim implements PurchasesUpdatedListener {

    // --------------------------------------------------------
    // Static flags and event queue.
    // ready: true once the billing client has connected to Play Store.
    // events: a thread-safe queue of result strings Python polls via pollEvent().
    // ConcurrentLinkedQueue is used because billing callbacks fire on
    // background threads while Python reads on a different thread.
    // --------------------------------------------------------
    public static volatile boolean ready = false;
    public static ConcurrentLinkedQueue<String> events = new ConcurrentLinkedQueue<>();

    private BillingClient client;   // The Google Play Billing client instance
    private Activity activity;      // Reference to the Android Activity (needed for purchase flow)

    // --------------------------------------------------------
    // Constructor — called from Python as: BillingShim(activity)
    // Builds the BillingClient with this class as the purchase listener.
    // enablePendingPurchases() is required by newer Billing Library versions.
    // --------------------------------------------------------
    public BillingShim(Activity activity) {
        this.activity = activity;

        client = BillingClient.newBuilder(activity)
                .setListener(this)           // This class handles onPurchasesUpdated()
                .enablePendingPurchases()    // Required — handles deferred payments
                .build();
    }

    // --------------------------------------------------------
    // start() — connects to the Google Play billing service.
    // Called from Python's init_iap().
    // Result is pushed to the event queue:
    //   "ready"       — connected successfully
    //   "init_failed" — connection failed
    //   "disconnected"— connection dropped (may retry)
    // --------------------------------------------------------
    public void start() {
        client.startConnection(new BillingClientStateListener() {
            @Override
            public void onBillingSetupFinished(BillingResult br) {
                if (br.getResponseCode() == BillingClient.BillingResponseCode.OK) {
                    ready = true;
                    events.add("ready");        // Python: safe to call buy() now
                } else {
                    events.add("init_failed");  // Python: billing unavailable
                }
            }

            @Override
            public void onBillingServiceDisconnected() {
                // Play Store service disconnected — may reconnect automatically
                ready = false;
                events.add("disconnected");
            }
        });
    }

    // --------------------------------------------------------
    // buy(productId) — launches the Google Play purchase dialog.
    // Called from Python's buy() function.
    //
    // Flow:
    //   1. Query Play Store for the product details (price, name etc.)
    //   2. If found, launch the purchase dialog (launchBillingFlow)
    //   3. Result is delivered to onPurchasesUpdated() below
    //
    // Events pushed on failure:
    //   "not_found:<productId>" — product ID doesn't exist in Play Console
    // --------------------------------------------------------
    public void buy(String productId) {
        if (!ready) {
            events.add("not_ready");  // buy() called before billing connected
            return;
        }

        // Build a query for the product ID
        QueryProductDetailsParams params =
                QueryProductDetailsParams.newBuilder()
                        .setProductList(List.of(
                                QueryProductDetailsParams.Product.newBuilder()
                                        .setProductId(productId)
                                        .setProductType(BillingClient.ProductType.INAPP)  // One-time purchase
                                        .build()
                        ))
                        .build();

        // Fetch product details from Play Store, then launch purchase dialog
        client.queryProductDetailsAsync(params, (br, list) -> {
            if (list.isEmpty()) {
                // Product ID not found — check spelling in Play Console
                events.add("not_found:" + productId);
                return;
            }

            // Launch the native Google Play purchase sheet
            BillingFlowParams flow =
                    BillingFlowParams.newBuilder()
                            .setProductDetailsParamsList(List.of(
                                    BillingFlowParams.ProductDetailsParams.newBuilder()
                                            .setProductDetails(list.get(0))
                                            .build()
                            ))
                            .build();

            client.launchBillingFlow(activity, flow);
            // Result arrives in onPurchasesUpdated() below
        });
    }

    // --------------------------------------------------------
    // onPurchasesUpdated() — called by Google Play when the
    // purchase dialog closes (success, cancel, or error).
    //
    // On success: consume the purchase (required for consumable items
    //             so the player can buy them again) and push a
    //             "purchased:<productId>" event.
    // On failure: push a "failed" event.
    // --------------------------------------------------------
    @Override
    public void onPurchasesUpdated(BillingResult br, List<Purchase> purchases) {
        if (br.getResponseCode() == BillingClient.BillingResponseCode.OK && purchases != null) {
            for (Purchase p : purchases) {
                consume(p);  // Consume each successful purchase
            }
        } else {
            // Player cancelled, or an error occurred
            events.add("failed");
        }
    }

    // --------------------------------------------------------
    // consume(purchase) — marks the purchase as consumed with Play Store.
    // This is required for consumable items (e.g. coins, lives) so the
    // player can purchase them again. For non-consumable items (e.g.
    // remove ads), you would use acknowledgePurchase() instead.
    //
    // On success: pushes "purchased:<productId>" to the event queue.
    // --------------------------------------------------------
    private void consume(Purchase p) {
        ConsumeParams params =
                ConsumeParams.newBuilder()
                        .setPurchaseToken(p.getPurchaseToken())
                        .build();

        client.consumeAsync(params, (br, token) -> {
            if (br.getResponseCode() == BillingClient.BillingResponseCode.OK) {
                // Purchase confirmed — Python should unlock the purchased content
                events.add("purchased:" + p.getProducts().get(0));
            } else {
                events.add("failed");
            }
        });
    }

    // --------------------------------------------------------
    // pollEvent() — called from Python each game loop frame.
    // Returns the next event string from the queue, or null if empty.
    // Python's poll_purchase() wraps this call.
    // --------------------------------------------------------
    public String pollEvent() {
        return events.poll();  // Returns null if queue is empty
    }
}
