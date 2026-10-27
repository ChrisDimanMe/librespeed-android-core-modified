# Changes against upstream

Upstream: `librespeed/speedtest-android`, revision `e3fd46b226f1c68d60969431c9147a1d61888a9d`, directory `app/src/main/java/com/fdossena/speedtest/core`. Of the 17 files, 9 were changed (`CHANGES.patch` is the exact diff); the other 8 are identical to upstream.

| File | Change |
|------|--------|
| `base/Connection.java` | TLS is layered over a plain socket that has connect and read timeouts, the handshake is run explicitly and the server name is verified with the platform hostname verifier (upstream did not verify it); a failed connection closes its socket; the missing CRLF after the `User-Agent` request header was added; `Accept-Language` is always sent; header names are lower-cased with `Locale.ROOT` |
| `download/Downloader.java`, `upload/Uploader.java`, `ping/Pinger.java` | errors caused by a deliberate stop are not reported; the connection is closed at the end; stop flags are `volatile`; `Pinger` also lower-cases text with `Locale.ROOT` |
| `download/DownloadStream.java`, `upload/UploadStream.java`, `ping/PingStream.java` | the initialization thread is kept and joined, instead of waiting in a polling loop for an object that may never be created when the connection fails; shared fields are `volatile` |
| `download/Downloader.java` | the first HTTP response headers are parsed before payload bytes are counted; an unexpected end of stream is an error |
| `serverSelector/ServerSelector.java`, `worker/SpeedtestWorker.java` | a stop flag is `volatile` |

Not changed in any way: the protocol, the measurement algorithm, the telemetry code (the app never enables telemetry) and the configuration classes.
