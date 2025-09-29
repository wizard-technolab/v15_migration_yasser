import contextlib
import OpenSSL.crypto
import tempfile

@contextlib.contextmanager
def pfx_to_pem(pfx_path, pfx_password):
    ''' Decrypts the .pfx file to be used with requests. '''

    # Create a temporary file with a '.pem' suffix for storing the converted PEM data
    with tempfile.NamedTemporaryFile(suffix='.pem', delete=False) as t_pem:
        # Open the temporary file for writing binary data
        with open(t_pem.name, 'wb') as f_pem:
            # Read the .pfx file's contents
            pfx = open(pfx_path, 'rb').read()
            # Encode the PFX password to bytes
            pfx_password_bytes = pfx_password.encode('utf-8')
            # Load the PFX file using OpenSSL
            p12 = OpenSSL.crypto.load_pkcs12(pfx, pfx_password_bytes)
            # Write the private key to the temporary PEM file
            f_pem.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, p12.get_privatekey()))
            # Write the certificate to the temporary PEM file
            f_pem.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, p12.get_certificate()))
            # Write CA certificates (if any) to the temporary PEM file
            ca = p12.get_ca_certificates()
            if ca is not None:
                for cert in ca:
                    f_pem.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
        # Yield the name of the temporary PEM file
        yield t_pem.name
