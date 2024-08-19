# -*- coding: utf-8 -*-
"""
VDES RX App.

This example application receives and displays data output by a VDES1000
transceiver.

@author: Jan Safar

Copyright 2024 GLA Research and Development Directorate

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""
# =============================================================================
# %% Import Statements
# =============================================================================
# Built-in Modules ------------------------------------------------------------
import socket

# Third-party Modules ---------------------------------------------------------
import yaml

# Local Modules ---------------------------------------------------------------
from vdes1000.utils import ts_print as print
from vdes1000.trx import VDESTransceiver

# =============================================================================
# %% Function Definitions
# =============================================================================
def recv_cbk_tgtd(address, data):
    # Do stuff with received data
    pass

# =============================================================================
# %% Class Definitions
# =============================================================================
class VDESProcessor:
    """
    Class to process data received from a VDES1000 transceiver.

    Currently this is used only to forward the received data to OpenCPN.

    Parameters
    ----------
    ip_address : str
        Destination address.
    port : int
        Destination port.

    """
    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port

        # Create the "send" UDP socket
        self.udp_send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def process_rx_data(self, address, data):
        """
        Process data received from the VDES1000.

        Intended to be used as a callback for receive events on dest_port_aist.

        Forwards the received data to the target address and port.

        Parameters
        ----------
        address : tuple (ip_address, port)
            Source address.
        data : str
            Received data.

        Returns
        -------
        None.

        """
        # Send data
        self.udp_send_sock.sendto(
            # data.encode(), # Use UTF-8 encoding
            data,
            (self.ip_address, self.port))

        print(
            "\nData sent to {:s}:{:d}: \n".format(self.ip_address, self.port),
            data,
            flush=True)

# =============================================================================
# %% Environment Initialisation
# =============================================================================
print(
"""
================================= VDES RX App =================================

 Receives and prints data output by a VDES transceiver. Additionally, forwards
 the received data to an Electronic Navigation Chart App.

 For the VDES transceiver configuration, see vdes_trx_2.yaml.

 Written for the General Lighthouse Authorities of the UK & Ireland,
 Jan Safar, 2021-2024.

===============================================================================

Initialising ------------------------------------------------------------------
""", flush=True)

# Initialise the VDES Processor; set the target IP address/port to that
# used by OpenCPN for inputting data over UDP
vp = VDESProcessor(ip_address="127.0.0.1", port=2947)

# Load the configuration file for VDES Transceiver 2
with open("vdes_trx_2.yaml") as file:
    trx_cfg = yaml.full_load(file)

# Initialise a VDES Transceiver object
vdes_trx = VDESTransceiver(
    cfg=trx_cfg,
    recv_cbk_tgtd=vp.process_rx_data)

# =============================================================================
# %% Main Programme "Loop"
# =============================================================================
print(
"""
Running -----------------------------------------------------------------------
""", flush=True)

# Wait for user to press Enter. Receive events are handled by the callback
# functions specified when initialising vdes_trx.
input("\nPress Enter to exit.")

print(
"""
Exiting -----------------------------------------------------------------------
""", flush=True)

# Close the recieving UDP sockets and stop the associated threads
vdes_trx.udp_interface.close()
