import socket
import re
import urllib.parse
import logging

logger = logging.getLogger("BHTTPRequestParser")


class BHTTPRequestParserError(Exception):
    pass


class BHTTPResponse:
    def __init__(self, response):
        self.raw_response = response
        self.good_headers = []
        self.bad_headers = []

        self.parse_headers()

    def parse_headers(self):
        headers = self.raw_response.split(b"\r\n\r\n")[0].decode()
        lines = headers.split("\r\n")

        logger.debug("Response: \n" + "\n".join(lines) + "\n" + "=" * 50)

        # Parse Header String
        header_parsed = re.findall(r"HTTP/([\d.]+)\s+(\d+)\s+([A-Za-z_\-]+)", lines[0])
        logger.info(f"header = {header_parsed}")

        if len(header_parsed) > 0:
            self.version, self.status_code, self.status = header_parsed[0]
            self.status_code = int(self.status_code)
        else:
            self.version, self.status_code, self.status = None, None, None

        if len(str(self.status_code)) != 3:
            self.version, self.status_code = None, None

        # Filter matches for "Key: Value"
        matches = list(filter(lambda x: re.match(r"([a-zA-Z0-9-_]+) *: *([\x00-\x7F]+)", x), lines[1:]))

        # Separate out good and bad
        self.bad_headers = list(filter(lambda x: re.match(r"([a-zA-Z0-9-_]+) *: *(.*)", x) is None, lines[1:]))
        self.good_headers = list(map(lambda x: re.findall(r"([a-zA-Z0-9-_]+) *: *(.*)", x)[0], matches))

        logger.info(f"failed headers: {self.bad_headers}")
        logger.info(f"good headers: {self.good_headers}")

    def print_header_parsed_status(self):
        if self.version is None:
            print("Invalid status line")
            return
        elif len(str(self.status_code)) != 3:
            print("Invalid status line")
            return
        else:
            print(f"HTTP version: {self.version}")
            print(f"Status: {self.status_code}")

        print(f"Number of valid headers: {len(self.good_headers)}")
        print(f"Number of invalid headers: {len(self.bad_headers)}")
        print("=" * 50)


class BHTTPRequestBuilder:
    # Sample request generator to validate real world scenario
    def __init__(self, host, extra_headers={}):
        """
        Class to build sample requests

        :param host: Hostname for the request header
        :param extra_headers: Unimplemented for now
        """
        self.http_request_header = [f'GET / HTTP/1.1',
                                    f'Host: {host}',
                                    f'User-Agent: BHTTPRequestParser(v0.0.1alpha)',
                                    f'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                                    f'Accept-Language: en-US,en;q=0.5',
                                    f'Accept-Encoding: gzip, deflate, br',
                                    f'DNT: 1',
                                    f'Upgrade-Insecure-Requests: 1',
                                    f'Connection: Close']

    @property
    def raw_string(self):
        """
        Returns Binary String containing the HTTP request header
        :return: str
        """
        # logger.debug(f"request: \n" + '\n'.join(self.http_request_header))
        r = "\r\n".join(self.http_request_header).encode() + b"\r\n\r\n"
        return r


class BHTTPRequestParser:
    def get_host_port(self, request_url):
        """
        Gets the host, and port from the URL string.
        :param request_url: Request url to be parsed
        :return:
        """
        url_parsed = urllib.parse.urlparse(request_url)
        # logger.info(url_parsed)
        host, port = re.findall(f"(.*):?(\d+)?", url_parsed.netloc)[0]
        if port == "":
            match url_parsed.scheme:
                case "https":
                    port = 443
                case "http":
                    port = 80
                case _:
                    raise BHTTPRequestParserError("Invalid request scheme. should be HTTP/HTTPS")
        else:
            port = int(port)

        return host, port, url_parsed

    def __init__(self):
        """
        BHTTPRequestParser is the base class for the http request. The manages the raw socket connection, stores the request and response for the request for future processing.

        The default implementation for the purpose of the assignment is to close the connection on every request. Also only the GET method is implemented.
        """
        self.http_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = None

    def get(self, request_url: str):

        """
        Get request
        :param request_url: request URL to send the HTTP request
        :return:
        """
        host, port, url_parse = self.get_host_port(request_url)

        self.http_socket.connect((host, port))

        request = BHTTPRequestBuilder(host, extra_headers={})

        self.http_socket.send(request.raw_string)
        data = b""
        while True:
            l = self.http_socket.recv(1024)
            if l == b"":
                break
            data += l

        # logger.info(f"response before processing: {data}")

        response = BHTTPResponse(data)
        return response

    def __del__(self):
        self.http_socket.close()
