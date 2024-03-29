# -*- coding: utf-8 -*-
"""
Minimal VDE Transmitter.

This example application demonstrates data transmission over VDE in a minimal
setting.

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
from bitstring import BitStream
from vdes1000.trx import VDESTransceiver

if __name__=='__main__':

    # VDES1000 Transceiver configuration (ip_address and dest_port_* must match
    # the configuration of your VDES1000 unit).
    cfg = {"user": {"ip_address": "10.0.2.203",
                    "dest_port_misc": 60030,
                    "dest_port_aist": 60031,
                    "dest_port_ccrd": 60033,
                    "listen_misc": True,
                    "listen_aist": True,
                    "listen_ccrd": False,
                    "talker_id": "1",
                    "udp_buffer_size": 4096,
                    "udp_verbosity": 3}}

    # Initialise a VDES Transceiver object. This also opens UDP sockets for
    # communication with the transceiver, as required.
    vdes_trx = VDESTransceiver(cfg)

    # Create a PI Data Payload to be transmitted over VDE
    # Note: The size must be an integer multiple of 8 bits, otherwise the
    # payload will be rejected by the VDES1000 unit.
    pi_data_payload_bs = BitStream(8 * 32)

    # Initiate an addressed data transfer
    vdes_trx.send_vde_data(pi_data_payload_bs, destination_id="992359599")

    input("\nPress Enter to exit.")

    # Close the UDP sockets when done
    vdes_trx.udp_interface.close()
