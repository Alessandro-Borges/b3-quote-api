How to provide a corporate CA to the container (for local testing)

Background
---------
If your company inspects HTTPS traffic, a proxy may present a company-signed certificate to clients. The proxy's CA must be trusted by the process performing HTTPS requests (here: Python inside the container). Containers normally rely on the base image CA bundle; if your company CA is missing you'll get SSL verification errors.

Options
------
1) Runtime mount (recommended for quick tests)
   - Place your company CA PEM next to the project root, named `company-ca.pem`.
   - Run the container mounting the file and updating the trust store at container start:

```bash
docker run -d --name b3-quote-api -p 8000:8000 \
  -v $(pwd)/company-ca.pem:/usr/local/share/ca-certificates/company-ca.crt:ro \
  b3-quote-api:latest /bin/sh -c "update-ca-certificates && uvicorn main:app --host 0.0.0.0 --port 8000"
```

2) Build-time inclusion (less flexible)
   - Copy `company-ca.pem` into the build context and modify the Dockerfile to COPY it earlier and run `update-ca-certificates` during build. Beware: this bakes the CA into the image.

Why runtime mount?
------------------
- Avoids rebuilding the image when the CA changes
- Keeps the corporate CA out of images pushed to registries
- Simple and suitable for testing

Security note
-------------
- Only add corporate CA to containers you control and only for development/testing.
- Never disable SSL verification globally in production.
