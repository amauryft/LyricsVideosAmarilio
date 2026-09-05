# Reassembling ainda-e-tempo-delivery.mp4

The render is 111 MB — over GitHub's 100 MB per-file limit — so it travels
as two parts. After downloading both parts, concatenate them:

macOS / Linux:

    cat ainda-e-tempo-delivery.mp4.part00 ainda-e-tempo-delivery.mp4.part01 > ainda-e-tempo-delivery.mp4

Windows (cmd):

    copy /b ainda-e-tempo-delivery.mp4.part00+ainda-e-tempo-delivery.mp4.part01 ainda-e-tempo-delivery.mp4

Verify (optional): SHA-256 of the reassembled file should be

    32c01ee104811d1164838514a627dec1459860b52cc90479d07b80c37d9879c5
