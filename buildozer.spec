# ============================================================
# buildozer.spec (IAP-relevant excerpt)
# Author: Wonder Kofi Junior (Almighty Prime)
# Project: Skiptrace (com.almightyprime.skiptrace)
#
# NOTE:
#   This is the same buildozer.spec used for Unity Ads.
#   Lines marked [IAP RELEVANT] are what you specifically need
#   for Google Play In-App Purchases to work.
#   See the full spec in the Ads tutorial package for all settings.
# ============================================================

[app]

title = Skiptrace
package.name = skiptrace

# [IAP RELEVANT] Your package domain must match exactly what you
# register in Google Play Console — this becomes your app's unique ID.
package.domain = com.almightyprime

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,ogg,mp3,ttf,xml
source.exclude_dirs = bin, .buildozer, aab_extracted, temp_aab, temp_check, manual_fix, fix_libs, p4a_recipes, venv
version = 0.3

# [IAP RELEVANT] 'jnius' is the Python-Java bridge that lets Python
# call BillingShim.java. 'android' provides Android API access.
requirements = python3==3.10.12,hostpython3==3.10.12,pygame,pyjnius

icon.filename = icon.png
orientation = landscape-reverse
fullscreen = 1
android.resizable = True
android.presplash_color = #000000

# [IAP RELEVANT] These permissions are required for IAP:
#   INTERNET — needed to connect to Play Store billing service
#   ACCESS_NETWORK_STATE / ACCESS_WIFI_STATE — required by billing library
#   com.android.vending.BILLING — the core IAP permission (without this,
#   Google Play will refuse to open the purchase dialog entirely)
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, com.android.vending.BILLING

android.api = 35
android.minapi = 21
android.ndk = 28b

# Required for Android 15+ devices
android.add_link_options = -Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384

android.ndk_api = 21
android.accept_sdk_license = True
android.manifest.extra_lines = android:resizeableActivity="true"
android.whitelist = com/google/android/play/core/tasks/*, com/google/android/play/core/appupdate/*, com/google/android/play/core/install/model/*

# [IAP RELEVANT] This tells Buildozer where to find BillingShim.java.
# Place it at: ./src/main/java/com/almightyprime/skiptrace/BillingShim.java
# Buildozer compiles it into the APK automatically during build.
android.add_src = src/main/java

# [IAP RELEVANT] The billing library dependency:
#   com.android.billingclient:billing:8.0.0 — Google Play Billing Library
#   androidx.fragment:fragment:1.8.9 — required by billing UI
#   com.google.android.gms:play-services-tasks — required by billing async ops
#
# NOTE: Keep the billing version as high as possible. Google Play enforces
# minimum billing library versions over time.
android.gradle_dependencies = com.unity3d.ads:unity-ads:4.12.2, com.android.billingclient:billing:8.0.0, androidx.fragment:fragment:1.8.9, com.google.android.play:app-update:2.1.0, com.google.android.play:review:2.0.1, com.google.android.play:review-ktx:2.0.1, com.google.android.gms:play-services-tasks:18.1.0

android.enable_androidx = True
android.enable_webview = True

# [IAP RELEVANT] MultiDex is required. The billing library + Unity Ads together
# push the method count well over Android's 64K limit. Without this, the
# build will fail with a "too many methods" error.
android.enable_multidex = True

android.gradle = 8.7
android.gradle_options = android.bundle.enableNativeLibraryCompression=false

# [IAP RELEVANT] google.com and jitpack are where the billing library is fetched.
android.gradle_repositories = "https://maven.google.com/", "https://jitpack.io", "https://repo.maven.apache.org/maven2", "https://unity3d.jfrog.io/artifactory/unity-ads"

android.manifest.orientation = sensorLandscape
android.manifest_attributes = android:extractNativeLibs="false"
android.meta_data = com.unity3d.ads.metadata.testmode=False, android.bundle.enableNativeLibraryCompression=false
android.archs = arm64-v8a
android.numeric_version = 10000
android.allow_backup = True

# [IAP RELEVANT] Google Play requires .aab format for new apps.
# IAP works correctly with .aab — no extra config needed.
android.release_artifact = aab

p4a.branch = master
p4a.local_recipes = ./p4a_recipes
p4a.bootstrap = sdl2


[buildozer]
log_level = 2
warn_on_root = 1
