#!/usr/bin/env python3
"""Rebuild the app with a modified LibreSpeed core.

Compiles the sources in ../src, converts them to a dex file and puts that dex FIRST in the app's APK, so
Android loads these classes instead of the ones shipped with the app. The result is aligned and signed
with YOUR key. Requirements: Python 3, a JDK (javac, 17 or newer), the Android SDK (platform android.jar
and build-tools with d8, zipalign and apksigner).

Example:
  python relink.py --apk base.apk --android-jar "$ANDROID_HOME/platforms/android-36/android.jar" \
      --keystore my.jks --ks-alias mykey --out base-relinked.apk
Optional: --build-tools <dir> (default: newest in $ANDROID_HOME/build-tools), --src <dir> (default ../src),
--ks-pass pass:<password> (default: asks apksigner to prompt).
"""
import argparse, os, re, shutil, subprocess, sys, tempfile, zipfile

SIGNATURE_ENTRY = re.compile(r"^META-INF/(MANIFEST\.MF|[^/]+\.(SF|RSA|DSA|EC))$", re.I)
DEX_ENTRY = re.compile(r"^classes(\d*)\.dex$")


def tool(build_tools, name):
    exe = {"nt": {"d8": "d8.bat", "apksigner": "apksigner.bat", "zipalign": "zipalign.exe"}}.get(os.name, {}).get(name, name)
    path = os.path.join(build_tools, exe)
    if not os.path.exists(path):
        sys.exit("Missing %s in %s" % (exe, build_tools))
    return path


def newest_build_tools():
    sdk = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not sdk:
        sys.exit("Set ANDROID_HOME or pass --build-tools")
    versions = sorted(os.listdir(os.path.join(sdk, "build-tools")), key=lambda v: [int(p) if p.isdigit() else 0 for p in re.split(r"[.\-]", v)])
    return os.path.join(sdk, "build-tools", versions[-1])


def run(cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apk", required=True, help="the app APK that contains classes.dex (base.apk for split installs)")
    ap.add_argument("--android-jar", required=True)
    ap.add_argument("--keystore", required=True)
    ap.add_argument("--ks-alias", required=True)
    ap.add_argument("--ks-pass")
    ap.add_argument("--out", required=True)
    ap.add_argument("--src", default=os.path.join(here, "..", "src"))
    ap.add_argument("--build-tools")
    args = ap.parse_args()
    bt = args.build_tools or newest_build_tools()
    work = tempfile.mkdtemp(prefix="relink-")
    try:
        # 1. compile the library sources
        sources = [os.path.join(d, f) for d, _, fs in os.walk(args.src) for f in fs if f.endswith(".java")]
        if not sources:
            sys.exit("No .java files under " + args.src)
        classes = os.path.join(work, "classes")
        os.makedirs(classes)
        run(["javac", "--release", "8", "-nowarn", "-cp", args.android_jar, "-d", classes] + sources)
        # 2. class files -> dex
        lib_jar = os.path.join(work, "lib.jar")
        run(["jar", "cf", lib_jar, "-C", classes, "."])
        dex_dir = os.path.join(work, "dex")
        os.makedirs(dex_dir)
        run([tool(bt, "d8"), "--lib", args.android_jar, "--min-api", "24", "--output", dex_dir, lib_jar])
        lib_dex = os.path.join(dex_dir, "classes.dex")
        # 3. new APK: the library dex becomes classes.dex (loaded first), the original dex files move up by one
        spliced = os.path.join(work, "spliced.apk")
        with zipfile.ZipFile(args.apk) as src, zipfile.ZipFile(spliced, "w") as dst:
            for info in src.infolist():
                if SIGNATURE_ENTRY.match(info.filename):
                    continue  # the old signature is invalid now; apksigner writes a new one
                data = src.read(info.filename)
                name = info.filename
                m = DEX_ENTRY.match(name)
                if m:
                    name = "classes%d.dex" % ((int(m.group(1)) if m.group(1) else 1) + 1)
                copy = zipfile.ZipInfo(name, info.date_time)
                copy.compress_type = info.compress_type
                copy.external_attr = info.external_attr
                dst.writestr(copy, data)
            with open(lib_dex, "rb") as f:
                dst.writestr(zipfile.ZipInfo("classes.dex", (2020, 1, 1, 0, 0, 0)), f.read(), zipfile.ZIP_DEFLATED)
        # 4. align and sign with the caller's key
        aligned = os.path.join(work, "aligned.apk")
        run([tool(bt, "zipalign"), "-p", "-f", "4", spliced, aligned])
        sign = [tool(bt, "apksigner"), "sign", "--ks", args.keystore, "--ks-key-alias", args.ks_alias]
        if args.ks_pass:
            sign += ["--ks-pass", args.ks_pass]
        run(sign + ["--out", args.out, aligned])
        run([tool(bt, "apksigner"), "verify", "--verbose", args.out])
        print("Done:", args.out)
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
