# LibreSpeed core: our modified version and how to rebuild the app with your own

This repository publishes the source code of a **modified copy of the LibreSpeed Android core** that is used in the app that links to this repository from its open-source licenses screen, together with instructions for replacing it. It is published because the library is licensed under the **GNU Lesser General Public License v3** (see `LICENSE`, and `COPYING-GPL-3.0.txt` for the GNU GPL v3 that it incorporates).

- Upstream project: <https://github.com/librespeed/speedtest-android> (revision `e3fd46b226f1c68d60969431c9147a1d61888a9d`)
- Copyright: Federico Dossena and LibreSpeed contributors.
- This folder contains only the library (`com.fdossena.speedtest.core`, 17 Java files). **It does not contain the source code of the app.** The app itself is not open source and is distributed through Google Play.

## Contents

| Path | What |
|------|------|
| `src/` | Full source of the modified core (the version shipped in the app) |
| `CHANGES.patch` | Unified diff against the upstream revision above (`patch -p1`, 9 files) |
| `CHANGES.md` | Plain-language list of what was changed and why |
| `tools/relink.py` | Script that rebuilds the app with a library built from `src/` |
| `LICENSE`, `COPYING-GPL-3.0.txt` | License texts |

## You may

Use, study, modify and redistribute this library under the LGPL v3, and use a modified version in place of the one in the app (below). The app's license terms do not restrict modification of this library or reverse engineering of the app for the purpose of debugging such modifications.

## Rebuilding the app with a modified library

The app's code is built with R8, but the names of all classes and members of `com.fdossena.speedtest.core` are kept unchanged on purpose, so a library built from (a modified version of) `src/` is interface-compatible with the shipped app. The script puts your build of the library in front of the one in the app and signs the result with your own key.

You need: Python 3, a JDK 17 or newer, the Android SDK (platform `android.jar`, build-tools with `d8`, `zipalign`, `apksigner`) and a signing key of your own (`keytool -genkeypair -v -keystore my.jks -alias mykey -keyalg RSA -keysize 2048 -validity 10000`).

1. Find the app's package name (Android Settings → Apps → the app → App details; it looks like `com.example.app`) and get its APK files from a device where it is installed:
   ```
   adb shell pm path <app package name>
   adb pull <each path shown> .
   ```
   Google Play installs the app as a `base.apk` plus smaller "split" APKs. The code is in `base.apk`.
2. Edit the sources under `src/` as you like (or leave them as they are to check that the process works).
3. Rebuild `base.apk`:
   ```
   python tools/relink.py --apk base.apk --android-jar "$ANDROID_HOME/platforms/android-36/android.jar" \
       --keystore my.jks --ks-alias mykey --out base-relinked.apk
   ```
4. Sign the other split APKs with the **same** key, so that all parts match:
   ```
   apksigner sign --ks my.jks --ks-key-alias mykey split_config.*.apk
   ```
5. Install. Because the signature is different, remove the original app first (this deletes its data):
   ```
   adb uninstall <app package name>
   adb install-multiple base-relinked.apk split_config.*.apk
   ```

If the app was installed as one single APK, only steps 3 and 5 are needed (`adb install base-relinked.apk`).

## Not covered

The app's signing key, the advertising and consent SDKs, and the app's own source code are not part of this publication. Android allows installing an app that is signed with another key, so no key is needed to run your rebuilt version.

## Contact

Questions about this publication: <!-- put the contact e-mail here -->
