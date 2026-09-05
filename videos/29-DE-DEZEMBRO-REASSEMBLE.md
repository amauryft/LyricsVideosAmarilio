# Reassembling 29-de-dezembro-delivery.mp4

The render is 134 MB — over GitHub's 100 MB per-file limit — so it travels
as two parts. After downloading both parts, concatenate them:

macOS / Linux:

    cat 29-de-dezembro-delivery.mp4.part00 29-de-dezembro-delivery.mp4.part01 > 29-de-dezembro-delivery.mp4

Windows (cmd):

    copy /b 29-de-dezembro-delivery.mp4.part00+29-de-dezembro-delivery.mp4.part01 29-de-dezembro-delivery.mp4

Verify (optional): SHA-256 of the reassembled file should be

    403d1bb60f2237f7ee307becf8153daa24ac03805c581911f7b4baa9d937eb77
