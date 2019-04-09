# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" Module for PT100 'poll' type plugin """

import copy
import json
import uuid
import logging
import RPi.GPIO as GPIO

from foglamp.plugins.south.pt100.max31865 import *
from foglamp.common import logger
from foglamp.plugins.common import utils


__author__ = "Ashwin Gopalakrishnan"
__copyright__ = "Copyright (c) 2018 Dianomic Systems"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'PT100 Poll Plugin',
        'type': 'string',
        'default': 'pt100',
        'readonly': 'true'
    },
    'assetNamePrefix': {
        'description': 'Asset prefix',
        'type': 'string',
        'default': "PT100/",
        'order': "1",
        'displayName': 'Asset Name Prefix'
    },
    'pins': {
        'description': 'Chip select pins to check',
        'type': 'string',
        'default': '8',
        'order': "3",
        'displayName': 'GPIO Pin'
    }
}

_LOGGER = logger.setup(__name__, level=logging.INFO)


def plugin_info():
    """ Returns information about the plugin.

    Args:
    Returns:
        dict: plugin information
    Raises:
    """

    return {
        'name': 'PT100 Poll Plugin',
        'version': '1.5.0',
        'mode': 'poll',
        'type': 'south',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(config):
    """ Initialise the plugin.

    Args:
        config: JSON configuration document for the South plugin configuration category
    Returns:
        handle: JSON object to be used in future calls to the plugin
    Raises:
    """
    data = copy.deepcopy(config)
    pins = config['pins']['value']
    pins = pins.split(',')
    probes = []
    for pin in pins:
        probes.append(max31865(csPin=int(pin)))
    _LOGGER.info('PT100 - MAX31865 with chip selects on pins {} initialized'.format(config['pins']['value']))
    data['probes'] = probes
    return data


def plugin_poll(handle):
    """ Extracts data from the sensor and returns it in a JSON document as a Python dict.

    Available for poll mode only.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
        returns a sensor reading in a JSON document, as a Python dict, if it is available
        None - If no reading is available
    Raises:
        Exception
    """
    probes = handle['probes']
    data = list()

    try:
        for probe in probes:
            temperature = probe.readTemp()
            data.append({
                'asset': '{}temperature{}'.format(handle['assetNamePrefix']['value'], probe.csPin),
                'timestamp': utils.local_timestamp(),
                'key': str(uuid.uuid4()),
                'readings': {
                    "temperature": temperature
                }
            })
    except (Exception, RuntimeError) as ex:
        _LOGGER.exception("PT100 exception: {}".format(str(ex)))
        raise ex
    else:
        _LOGGER.debug("PT100 reading: {}".format(json.dumps(data)))
        return data


def plugin_reconfigure(handle, new_config):
    """  Reconfigures the plugin

    it should be called when the configuration of the plugin is changed during the operation of the South service;
    The new configuration category should be passed.

    Args:
        handle: handle returned by the plugin initialisation call
        new_config: JSON object representing the new configuration category for the category
    Returns:
        new_handle: new handle to be used in the future calls
    Raises:
    """
    _LOGGER.info("Old config for PT100 plugin {} \n new config {}".format(handle, new_config))
    new_handle = copy.deepcopy(new_config)
    return new_handle


def plugin_shutdown(handle):
    """ Shutdowns the plugin doing required cleanup, to be called prior to the South service being shut down.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
    Raises:
    """
    GPIO.cleanup()
    _LOGGER.info('PT100 poll plugin shut down.')
