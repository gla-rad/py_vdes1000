# -*- coding: utf-8 -*-
"""
VDES TX App.

This example application allows the user to send AIS, VDES-ASM and VDE transmit
commands to a VDES1000 transceiver and displays the response.

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
from time import sleep

# Third-party Modules ---------------------------------------------------------
import yaml
from bitstring import BitStream

# Local Modules ---------------------------------------------------------------
from vdes1000.utils import ts_print as print
from iec_62320.part_1.sentences import BCGSentence
from rec_itu_r_m_1371.messages import AISMessage21, AISMessage8
from rec_itu_r_m_1371.asm_payloads import SampleASMPayload1
from vdes1000.trx import VDESTransceiver

# =============================================================================
# %% Function Definitions
# =============================================================================
def recv_cbk_tgtd(address, data):
    # Do stuff with received data
    pass

def user_input(prompt, var_type, limits=None, default=None):
    """
    Display an input prompt, read input, check data type and limits and if
    OK, return the input value; if not OK, repeat the prompt.

    Parameters
    ----------
    prompt : str
        User prompt. If not None, limits and default value are appended.
    var_type : str
        Type of the input variable.
    limits : list, optional
        Limits for numerical inputs [lower lim., upper lim.].
        The default is None.
    default : var_type, optional
        Default value to return if no input provided. The default is None.

    Returns
    -------
    value : var_type
        Input value.
    """
    done = False

    if limits is not None:
        prompt += " ({0}-{1})".format(limits[0], limits[1])

        if default is not None:
            prompt += ","

    if default is not None:
        prompt += " [" + str(default) + "]"

    prompt += ": "

    while not done:
        value = input(prompt)
        if (value == "") and (default is not None):
            done = True
            value = default
        if var_type == "int":
            try:
                value = int(value)
                if (limits is None) or (limits[0] <= value <= limits[1]):
                    done = True
            except:
                pass
        elif var_type == "str":
            done = True
        else:
            raise ValueError("Unknown variable type!")
    return value

# =============================================================================
# %% Class Definitions
# =============================================================================


# =============================================================================
# %% Environment Initialisation
# =============================================================================
print(
"""
================================= VDES TX App =================================

 Initiate transmissions from a VDES1000 transceiver and observe the response.

 For the VDES transceiver and message configuration, see vdes_trx_1.yaml and
 messages.yaml, respectively.

 Written for the General Lighthouse Authorities of the UK & Ireland,
 Jan Safar, 2021-2024.

===============================================================================

Initialising ------------------------------------------------------------------
""", flush=True)

# Load the configuration file for VDES Transceiver 1
with open("vdes_trx_1.yaml") as file:
    trx_cfg = yaml.full_load(file)

# Load the message configuration file
with open("messages.yaml") as file:
    messages = yaml.full_load(file)

# Initialise an AIS Message 21 object
ais_msg_21 = AISMessage21(**messages["ais_msg_21"])

# Initialise the ASM-related objects
ais_asm_payload = SampleASMPayload1(
    n_app_data_bytes=messages["ais_asm_payload"]["n_app_data_bytes"])

ais_msg_8 = AISMessage8(
    source_id=messages["ais_msg_8"]["source_id"],
    payload=ais_asm_payload)

# VDES-ASM payload - may be larger than the AIS one
vdes_asm_payload = SampleASMPayload1(
    n_app_data_bytes=messages["vdes_asm_payload"]["n_app_data_bytes"])

# Create a PI Data Payload to be transmitted over VDE
# Note: The size must be an integer multiple of 8 bits.
pi_data_payload_bs = BitStream(384*2)

# AIS Spoofing Test A
# Initialise AIS Message 21 objects
ais_spoof_a_msgs = [
    # AISMessage21(**messages["ais_spoof_a_msg_21_1"]),
    # AISMessage21(**messages["ais_spoof_a_msg_21_2"]),
    # AISMessage21(**messages["ais_spoof_a_7msg_21_3"]),
    # AISMessage21(**messages["ais_spoof_a_msg_21_4"]),
    AISMessage21(**messages["ais_spoof_a_msg_21_5"]),
    AISMessage21(**messages["ais_spoof_a_msg_21_6"]),
    AISMessage21(**messages["ais_spoof_a_msg_21_7"])]

# AIS Spoofing Test B
# Initialise an AIS Message 21 object
ais_spoof_b_msg_21 = AISMessage21(**messages["ais_spoof_b_msg_21"])

# Initialise a VDES Transceiver object
vdes_trx = VDESTransceiver(
    cfg=trx_cfg,
    recv_cbk_tgtd=recv_cbk_tgtd)

# AIS transmit channel
ais_tx_ch = ["AIS 1", "AIS 2"]
i_ais_tx_ch = 0

# VDES-ASM transmit channel
asm_tx_ch = ["ASM 1", "ASM 2"]
i_asm_tx_ch = 0

sleep(1)
# =============================================================================
# %% Main Programme Loop
# =============================================================================
print(
"""
Running -----------------------------------------------------------------------""",
flush=True)

while True:

    print(
f"""
0 - Exit
1 - Enable RATDMA on AIS channels
2 - Query AIS base station configuration
3 - Transmit AIS Message 21 (AtoN) on {ais_tx_ch[i_ais_tx_ch]}
4 - Transmit AIS Message 8 (Binary Broadcast Message on {ais_tx_ch[i_ais_tx_ch]}
5 - Transmit a VDES-ASM Broadcast Message on {asm_tx_ch[i_asm_tx_ch]}
6 - Send an Addressed VDE Data Transmission
7 - AIS Spoofing Test A
8 - AIS Spoofing Test B
9 - Toggle AIS channel
10 - Toggle ASM channel""", flush=True)

    # Ask for user input and act on it
    ui = user_input("\nSelect action", "int", limits=[0,9])

    if ui == 0:
        print(
"""
Exiting -----------------------------------------------------------------------
""", flush=True)
        break

    elif ui == 1:
        # Enable RATDMA on AIS channels
        vdes_trx.configure_ais_base_station(
                "BASE1",
                ratdma_control=1,
                talker_id="AB")

    elif ui == 2:
        # Query AIS base station configuration
        vdes_trx.query_ais_base_station_cfg("AI", "AB")

    elif ui == 3:
        # Send AIS Message 21 on the requested channel using RATDMA
        # vdes_trx.send_ais_msg_ratdma(
        #     msg_bs=ais_msg_21.bitstream,
        #     channel=ais_tx_ch[i_ais_tx_ch])
        vdes_trx.send_ais_msg_fatdma(
            msg_bs=ais_msg_21.bitstream,
            channel=ais_tx_ch[i_ais_tx_ch])

    elif ui == 4:
        # Send AIS binary broadcast message on the requested channel
        # and using the requested method
        if trx_cfg["user"]["ais_bin_broadcast_method"] == "vdm":
            vdes_trx.send_ais_msg_ratdma(
                msg_bs=ais_msg_8.bitstream,
                channel=ais_tx_ch[i_ais_tx_ch])

        elif trx_cfg["user"]["ais_bin_broadcast_method"] == "bbm":
            vdes_trx.send_ais_binary_broadcast(
                asm_payload_bs=ais_asm_payload.bitstream,
                channel=ais_tx_ch[i_ais_tx_ch],
                msg_id=8)

        else:
            print("Unknown AIS binary broadcast method!")

    elif ui == 5:
        # Send a VDES-ASM Broadcast Message on the requested channel
        vdes_trx.send_asm_broadcast(
            asm_payload_bs=vdes_asm_payload.bitstream,
            source_id=messages["asm_broadcast"]["source_id"],
            channel=asm_tx_ch[i_asm_tx_ch],
            transmission_format=messages["asm_broadcast"]["transmission_format"])

    elif ui == 6:
        # Initiate an addressed VDE data transmission
        vdes_trx.send_vde_data(
            pi_data_payload_bs=pi_data_payload_bs,
            destination_id="992359599")

    # elif ui == 7:
    #     # Testing
    #     vdes_trx.udp_interface.send_tgtd_iec_msg("\\g:1-1-47,s:tt00,n:47*40\\$ABAIQ,BCG*30\r\n")

    elif ui == 7:
        # AIS Spoofing Test A
        # Send AIS Messages 21 on the requested channel using RATDMA
        # vdes_trx.send_ais_msg_ratdma(
        #     msg_bs=ais_msg_21.bitstream,
        #     channel=ais_tx_ch[i_ais_tx_ch])
        for ais_msg in ais_spoof_a_msgs:
            vdes_trx.send_ais_msg_fatdma(
                msg_bs=ais_msg.bitstream,
                channel=ais_tx_ch[i_ais_tx_ch])
            # FIXME: This is a quick and dirty fix to prevent the transceiver
            # from mixing up the messages.
            sleep(3)

    elif ui == 8:
        # AIS Spoofing Test A
        # Send AIS Messages 21 on the requested channel using RATDMA
        vdes_trx.send_ais_msg_fatdma(
            msg_bs=ais_spoof_b_msg_21.bitstream,
            channel=ais_tx_ch[i_ais_tx_ch])

    elif ui == 9:
        i_ais_tx_ch = (i_ais_tx_ch + 1) % len(ais_tx_ch)

    elif ui == 10:
        i_asm_tx_ch = (i_asm_tx_ch + 1) % len(asm_tx_ch)

    # Provide time for communications to happen before printing the menu again
    if 0 < ui < 9:
        sleep(5)

# Close the recieving UDP sockets and stop the associated threads
vdes_trx.udp_interface.close()
