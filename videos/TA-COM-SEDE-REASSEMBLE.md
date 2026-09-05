# Reassembling ta-com-sede-delivery.mp4

The render is 114 MB — over GitHub's 100 MB per-file limit — so it travels
as two parts. After downloading both parts, concatenate them:

macOS / Linux:

    cat ta-com-sede-delivery.mp4.part00 ta-com-sede-delivery.mp4.part01 > ta-com-sede-delivery.mp4

Windows (cmd):

    copy /b ta-com-sede-delivery.mp4.part00+ta-com-sede-delivery.mp4.part01 ta-com-sede-delivery.mp4

Verify (optional): SHA-256 of the reassembled file should be

    3f28a558005f532a54319e5bbb3f482b0863f960827b7900e369647dc6b40865
