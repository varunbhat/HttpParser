from HttpHeaderParser import BHTTPRequestParser

import logging

# logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    example_host = "http://www.broadcom.com/"

    request = BHTTPRequestParser()
    r = request.get(example_host)
    r.print_header_parsed_status()
