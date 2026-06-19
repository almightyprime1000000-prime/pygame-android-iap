# ============================================================
# iap.py
# Author: Wonder Kofi Junior (Almighty Prime)
# Project: Skiptrace (com.almightyprime.skiptrace)
#
# PURPOSE:
#   This module handles In-App Purchases (IAP) in a Python/Pygame
#   Android game using the Google Play Billing Library.
#
# HOW IT WORKS (overview):
#   1. We grab the Android Activity (the running app window) via Pyjnius
#   2. We load BillingShim.java — our custom Java class that wraps
#      the Google Play Billing Library in a Python-friendly way
#   3. Python calls init_iap() once at startup, then buy() when the
#      player wants to purchase something, and polls poll_purchase()
#      each frame to check if a purchase completed
#
# DEPENDENCIES:
#   - pyjnius (pip install pyjnius) — bridges Python <-> Java on Android
#   - Google Play Billing Library (added as a dependency in build.gradle)
#   - BillingShim.java (must be compiled into the Android APK)
#   - Buildozer or similar tool to compile the Android APK
#
# IMPORTANT — Google Play Setup:
#   Before IAP works, you must:
#   1. Create your in-app products in the Google Play Console
#   2. Use the exact product IDs you set there when calling buy()
#   3. Test with a signed APK uploaded to Play Console's testing track
# ============================================================

from jnius import autoclass, cast

# ============================================================
# STEP 1 — Get the Android Activity
# The Activity is the Android equivalent of the "app window".
# Google Play Billing needs it to launch the purchase dialog.
# SDL is the graphics layer used by Pygame on Android.
# ============================================================
SDLActivity = autoclass('org.libsdl.app.SDLActivity')
activity = cast('android.app.Activity', SDLActivity.mSingleton)

# ============================================================
# STEP 2 — Load BillingShim Java class via Pyjnius
# BillingShim.java wraps the Google Play Billing Library and
# exposes a simple event queue that Python can poll.
# ============================================================
BillingShim = autoclass("com.almightyprime.skiptrace.BillingShim")

# Holds the BillingShim instance after init_iap() is called
billing = None

# ============================================================
# STEP 3 — Public API
# These are the three functions your game code needs to call.
# ============================================================

def init_iap():
    """
    Initialize the Google Play Billing client.
    Call this once when your game starts (e.g. in your main setup).
    The billing client connects asynchronously — poll poll_purchase()
    until you receive a "ready" event before calling buy().

    Events you may receive after calling this:
      "ready"       — billing is connected and ready to use
      "init_failed" — connection failed (check internet / Play Store)
    """
    global billing
    billing = BillingShim(activity)
    billing.start()
    print("IAP: INIT SENT")

def buy(product_id):
    """
    Launch the Google Play purchase dialog for a given product.
    - product_id: the exact product ID string from your Google Play Console
                  e.g. "remove_ads" or "coin_pack_100"

    The purchase runs asynchronously. Poll poll_purchase() each frame
    to check the result. Must be called on the UI thread (handled here).

    Example:
        buy("remove_ads")
    """
    if not BillingShim.ready:
        # Billing client not connected yet — init_iap() may still be connecting
        print("IAP: NOT READY")
        return
    # runOnUiThread is required — Google Play Billing must launch from the UI thread
    activity.runOnUiThread(lambda: billing.buy(product_id))

def poll_purchase():
    """
    Check if a purchase event has occurred since the last call.
    Call this every game loop frame to handle purchase results.

    Returns one of:
      "ready"              — billing client just connected (safe to call buy())
      "purchased:<id>"     — purchase successful, e.g. "purchased:remove_ads"
                             Unlock the content for this product ID
      "not_found:<id>"     — product ID not found in Play Console
                             Check your product ID spelling
      "failed"             — purchase was cancelled or failed
      "not_ready"          — buy() was called before billing was ready
      "disconnected"       — billing client lost connection to Play Store
      None                 — no new events, keep waiting

    Example game loop usage:
        event = poll_purchase()
        if event and event.startswith("purchased:"):
            product = event.split(":")[1]
            if product == "remove_ads":
                disable_ads()
    """
    event = billing.pollEvent()
    return event
