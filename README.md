# Google Play In-App Purchases in Python/Pygame (Android)
### A real-world implementation by Wonder Kofi Junior (AlmightyPrime)
### From the game: Skiptrace — https://play.google.com/store/apps/details?id=com.almightyprime.skiptrace

---

## What this package contains

This is the complete, working implementation of Google Play In-App Purchases (IAP) inside a Python/Pygame Android game. Every file here is extracted from Skiptrace — a real game live on the Google Play Store. This is not a proof of concept. It runs in production.

```
skiptrace_iap_tutorial/
│
├── python/
│   └── iap.py                   ← The Python IAP wrapper (copy into your project)
│
├── java/
│   └── BillingShim.java         ← Custom Java billing wrapper (compile into your APK)
│
├── buildozer/
│   └── buildozer.spec           ← Buildozer config with [IAP RELEVANT] markers
│
└── example_usage/
    └── example_usage.py         ← Full game loop integration pattern
```

---

## Why a Java shim is needed

The Google Play Billing Library uses complex asynchronous Java callbacks that Pyjnius (the Python-Java bridge) cannot reliably implement in Python. Billing events fire on background threads at unpredictable times, which causes crashes or silent failures when handled directly in Python.

The fix: wrap all billing logic in a Java class (`BillingShim.java`) that pushes results into a thread-safe event queue. Python polls the queue each game frame using `poll_purchase()` — simple, safe, and crash-free.

---

## Quick start (4 steps)

### 1. Copy the Python file
Place `iap.py` in your project root (same folder as `main.py`).

### 2. Add the Java shim
Place `BillingShim.java` in:
```
your_project/src/main/java/com/yourpackage/yourapp/BillingShim.java
```
Update the `package` line at the top to match your own package name.

Then in `buildozer.spec`:
```
android.add_src = src/main/java
```

### 3. Add the Gradle dependency and permission
In `buildozer.spec`:
```
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, com.android.vending.BILLING
android.gradle_dependencies = com.android.billingclient:billing:8.0.0, androidx.fragment:fragment:1.8.9
android.enable_multidex = True
```

### 4. Set up your products in Google Play Console
- Go to Play Console → Your App → Monetize → Products → In-app products
- Create a product for each item (e.g. "fruitpack1")
- The product ID must exactly match what you pass to `iap.buy()`
- Products only work on signed APKs uploaded to a testing track

---

## Using it in your game

```python
import iap

# At startup (once)
iap.init_iap()

# When player clicks "Buy"
iap.buy("your_product_id")

# Every frame in your game loop
result = iap.poll_purchase()
if result:
    if result.startswith("purchased:"):
        product_id = result.split(":")[1]
        # Give the player their reward
    elif result == "failed":
        # Purchase cancelled or failed
    elif result == "ready":
        pass  # Billing connected — swallow silently
```

See `example_usage/example_usage.py` for the full pattern including cooldown guards, every event type handled, and the UI feedback message system from Skiptrace.

---

## Important notes

- IAP **only works on a signed APK/AAB** uploaded to Google Play's testing track
- It will NOT work on a debug build run directly via `buildozer android debug`
- Make sure `com.android.vending.BILLING` is in your permissions or purchases will silently fail
- The `BillingShim` uses `consumeAsync()` for consumable items (things the player can buy multiple times). For non-consumable items (e.g. "remove ads"), you would use `acknowledgePurchase()` instead — see comments in `BillingShim.java`

---

## Also available: Unity Rewarded Ads

If you need Unity Rewarded Ads for your Pygame Android game, a separate tutorial package is available covering `unity_ads_android.py`, `ShowListenerShim.java`, and full integration — also extracted from Skiptrace.

---

## About this implementation

Built by **Wonder Kofi Junior** (AlmightyPrime), a solo developer from Ghana.
Two years of learning, failing, and finishing — on midnight internet data.

##Support The Project

If this repository helped you integrate In App Purchase into your Pygame Android game, or if you'd like to try a fully integrated production example on Google Play, please consider:

Starring this repository
Sharing it with other developers
Downloading and rating Skiptrace on Google Play

Play Store: https://play.google.com/store/apps/details?id=com.almightyprime.skiptrace

Developer story: https://www.fixgamingchannel.com/from-a-jackie-chan-movie-to-google-play-the-story-of-skiptrace/

Your support helps me continue creating tutorials and open-source resources for the Pygame Android community.
