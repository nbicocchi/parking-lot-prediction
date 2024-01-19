import base64
import logging
from urllib.request import Request, build_opener, BaseHandler

from utilities.auth_info import read_auth_info

auth_info = read_auth_info()
SFDE_USERNAME = auth_info['bosch_username']
SFDE_PASSWORD = auth_info['bosch_password']
sfdeProject = auth_info['bosch_project']
logger = logging.getLogger(__name__)


def basics_auth(username, password):
    """ Method which return a base 64 basic authentication
    :param username: your SFDE username
    :param password: your password username
    :return: returns string
    """
    credential = username + ':' + password
    encoded_credential = credential.encode('ascii')
    b_encoded_credential = base64.b64encode(encoded_credential)
    b_encoded_credential = b_encoded_credential.decode('ascii')
    b_auth = b_encoded_credential
    return 'Basic {}'.format(b_auth)


def make_request(server_url, post_data=None):
    """ Method which handel a request and return response as json
    :param server_url:  the url for the request
    :param post_data: post data for Post method
    :return: content
    """
    handler = BaseHandler()
    opener = build_opener(handler)
    r = Request(server_url + sfdeProject)

    sfde_b_auth = basics_auth(SFDE_USERNAME, SFDE_PASSWORD)
    r.add_header('Authorization', sfde_b_auth)
    r.add_header('Content-Type', 'application/json')
    r.add_header('Accept', 'application/json')

    r_data = post_data
    r.data = r_data

    handle = opener.open(r)
    content = handle.read().decode('utf8')
    return content


def send_data(payload):
    try:
        # Server and the api service details
        server = 'https://bosch-iot-insights.com'
        service_base_url = '/data-recorder-service/'
        service = 'v2/'
        url = server + service_base_url + service  # construction of the final url for the first POST request
        data = payload.encode('ascii')  # encoding format is ascii for the initial POST request
        res = make_request(url, data)

        logger.debug(res)
        logger.info('Data was send to Project: {}'.format(sfdeProject))

    except IOError:
        pass
