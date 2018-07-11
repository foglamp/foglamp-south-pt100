# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" Module for PT100 'poll' type plugin """

import copy
import datetime
import json
import uuid
import RPi.GPIO as GPIO

from foglamp.plugins.south.pt100.max31865 import *
from foglamp.common import logger
from foglamp.plugins.common import utils
from foglamp.services.south import exceptions


__author__ = "Ashwin Gopalakrishnan"
__copyright__ = "Copyright (c) 2018 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_DEFAULT_CONFIG = {
    'plugin': {
         'description': 'PT100 Poll Plugin',
         'type': 'string',
         'default': 'pt100'
    },
    'pins': {
        'description': 'Chip select pins to check',
        'type': 'string',
        'default': '8'
    },
    'pollInterval': {
        'description': 'The interval between poll calls to the South device poll routine expressed in milliseconds.',
        'type': 'integer',
        'default': '5000'
    },
}

_LOGGER = logger.setup(__name__, level=20)


def plugin_info():
    """ Returns information about the plugin.

    Args:
    Returns:
        dict: plugin information
    Raises:
    """

    return {
        'name': 'PT100 Poll Plugin',
        'version': '1.0',
        'mode': 'poll',
        'type': 'south',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(config):
    """ Initialise the plugin.

    Args:
        config: JSON configuration document for the South device configuration category
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
        DataRetrievalError
    """
    probes = handle['probes']
    time_stamp = str(datetime.datetime.now(tz=datetime.timezone.utc))
    data = list()

    try:
        for probe in probes:
            temperature = probe.readTemp()
            time_stamp = str(datetime.datetime.now(tz=datetime.timezone.utc))
            data.append({
                'asset': 'PT100/temperature{}'.format(probe.csPin),
                'timestamp': time_stamp,
                'key': str(uuid.uuid4()),
                'readings': {
                    "temperature": temperature
                }
            })
    except (Exception, RuntimeError, pexpect.exceptions.TIMEOUT) as ex:
        _LOGGER.exception("PT100 exception: {}".format(str(ex)))
        raise exceptions.DataRetrievalError(ex)

    _LOGGER.debug("PT100 reading: {}".format(json.dumps(data)))
    return data


def plugin_reconfigure(handle, new_config):
    """  Reconfigures the plugin

    it should be called when the configuration of the plugin is changed during the operation of the South device service;
    The new configuration category should be passed.

    Args:
        handle: handle returned by the plugin initialisation call
        new_config: JSON object representing the new configuration category for the category
    Returns:
        new_handle: new handle to be used in the future calls
    Raises:
    """
    _LOGGER.info("Old config for PT100 plugin {} \n new config {}".format(handle, new_config))

    # Find diff between old config and new config
    diff = utils.get_diff(handle, new_config)

    # Plugin should re-initialize and restart if key configuration is changed
    if 'pollInterval' in diff:
        new_handle = copy.deepcopy(new_config)
        new_handle['restart'] = 'no'
    else:
        new_handle = copy.deepcopy(handle)
        new_handle['restart'] = 'no'
    return new_handle


def _plugin_stop(handle):
    """ Stops the plugin doing required cleanup, to be called prior to the South device service being shut down.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
    Raises:
    """
    GPIO.cleanup()
    _LOGGER.info('PT100 poll plugin stop.')


def plugin_shutdown(handle):
    """ Shutdowns the plugin doing required cleanup, to be called prior to the South device service being shut down.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
    Raises:
    """
    _plugin_stop(handle)
    _LOGGER.info('PT100 poll plugin shut down.')
