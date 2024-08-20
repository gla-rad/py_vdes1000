# -*- coding: utf-8 -*-
"""
VDES1000 Transceiver Module.

This module provides high-level interfaces for transmitting [and receiving]
data over AIS, VDES-ASM and VDE.

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
import time

# Third-party Modules ---------------------------------------------------------

# Local Modules ---------------------------------------------------------------
from iec_61162.part_1.sentences import QSentence
from iec_61162.part_1.sentences import SentenceGenerator as AISMobSentenceGenerator
from iec_62320.part_1.sentences import BCGSentence
from iec_62320.part_1.sentences import SentenceGenerator as AISBaseSentenceGenerator
from iec_pas_63343.sentences import SentenceGenerator as ASMSentenceGenerator
from vdes1000.sentences import SentenceGenerator as VDESentenceGenerator
from iec_61162.part_450.messages import MessageGenerator
from vdes1000.udp import UDPInterface

# =============================================================================
# %% Function Definitions
# =============================================================================


# =============================================================================
# %% Class Definitions
# =============================================================================
class VDESTransceiver():
    """
    A class to control and receive data from a VDES1000 unit.

    Parameters
    ----------
    cfg : dict
        Transceiver configuration. See vdes_trx_X.yaml
    recv_cbk_tgtd : function, optional
        Receive event callback function for dest_port_tgtd.

        Expected arguments:

        address : tuple, (ip_address, port)
            Source address.
        data : str
            Received data.

        The default is None.

    Returns
    -------
    None.

    """
    def __init__(self, cfg, recv_cbk_tgtd=None):
        # Store configuration
        self.cfg = cfg

        # Initialise an AIS Base Statopm Sentence Generator
        self.ais_base_sg = AISBaseSentenceGenerator()

        # Initialise an AIS Mobile Station Sentence Generator
        self.ais_mob_sg = AISMobSentenceGenerator()

        # Initialise an ASM Sentence Generator
        self.asm_sg = ASMSentenceGenerator()

        # Initialise a VDE Sentence Generator
        self.vde_sg = VDESentenceGenerator()

        # Initialise an IEC 61162-450 Message Generator
        self.iec_61162_450_mg = MessageGenerator(
            source_id=cfg["user"]["talker_id"])

        # Initialise a VDES1000 UDP interface
        self.udp_interface = UDPInterface(
            ip_address=cfg["user"]["ip_address"],
            dest_port_tgtd=cfg["user"]["dest_port_tgtd"],
            listen_tgtd=cfg["user"]["listen_tgtd"],
            recv_cbk_tgtd=recv_cbk_tgtd,
            buffer_size=cfg["user"]["udp_buffer_size"],
            verbosity=cfg["user"]["udp_verbosity"])

        # Wait for the UDP receiving threads to start
        while (self.udp_interface.n_rx_threads <
               self.udp_interface.n_listening_ports):
            time.sleep(1)

    def configure_ais_base_station(
            self,
            unique_id,
            tx_power_a=None,
            tx_power_b=None,
            vdl_retries=None,
            vdl_repeat=None,
            ratdma_control=None,
            utc_source=None,
            ads_interval=None,
            talker_id="AB",
            rx_channel_a=2087,
            rx_channel_b=2088,
            tx_channel_a=2087,
            tx_channel_b=2088):

        # Create a BCG Sentence
        sentence = BCGSentence(
            unique_id=unique_id,
            tx_power_a=tx_power_a,
            tx_power_b=tx_power_b,
            vdl_retries=vdl_retries,
            vdl_repeat=vdl_repeat,
            ratdma_control=ratdma_control,
            utc_source=utc_source,
            ads_interval=ads_interval,
            talker_id=talker_id,
            rx_channel_a=rx_channel_a,
            rx_channel_b=rx_channel_b,
            tx_channel_a=tx_channel_a,
            tx_channel_b=tx_channel_b,
            sentence_status="C")

        # Send the BCG sentence through the IEC 61162-450 processing
        iec_messages = self.iec_61162_450_mg.generate_msg([[sentence]])

        # Send the IEC 61162-450 Message via UDP to the VDES1000
        for msg in iec_messages:
            self.udp_interface.send_tgtd_iec_msg(msg.string)

    def query_ais_base_station_cfg(
            self,
            src_talker_id="AI",
            dest_talker_id="AB"):
        """
        Query the AIS Base Station configuration.

        """
        # Create a Q sentence
        sentence = QSentence(
            src_talker_id=src_talker_id,
            dest_talker_id=dest_talker_id,
            formatter="BCG")

        # Send the sentences through the IEC 61162-450 processing
        iec_messages = self.iec_61162_450_mg.generate_msg([[sentence]])

        # Send the IEC 61162-450 Messages via UDP to the VDES1000
        for msg in iec_messages:
            self.udp_interface.send_tgtd_iec_msg(msg.string)

    def send_ais_msg_fatdma(
            self,
            msg_bs,
            channel,
            unique_id="",
            utc_hhmm="",
            start_slot="",
            priority=2):
        """
        Send an arbitrary AIS message using FATDMA.

        Issues a TSA-VDM sentence pair to send the AIS message in a specified
        time slot.

        Note: When the TSA-VDM RATDMA feature is enabled on the VDES1000
        (FeatureMask bit 7) and utc_hhmm and start_slot are both set to null
        (""), the unit will use RATDMA. However, this feature is not standards
        compliant and will likely be removed in future firmware updates.

        Parameters
        ----------
        msg_bs : bitstring.BitStream
            AIS message bitstream, formatted as per Rec. ITU-R M.1371.
        channel : str
            Channel selection ('AIS 1' or 'AIS 2').
        unique_id : str, optional
            Base station's unique ID. Maximum of 15 characters.
            The default is "".
        utc_hhmm : str, optional
            UTC frame hour and minute of the requested transmission.
            The default is "".
        start_slot : str, optional
            Start slot number of the requested transmission. The default is "".
        priority : int, optional
            Transmission priority (0-2). Lower number corresponds to higher
            priority. The default is 2.

        Raises
        ------
        ValueError
            if an unknown channel value is used.

        Returns
        -------
        None.

        """
        channel_dict = {"AIS 1": "A", "AIS 2": "B"}

        if channel not in channel_dict:
            raise ValueError("Unknown channel value.")

        # Send the message down the presentation layer
        sentences = self.ais_base_sg.generate_tsa_vdm(
            msg_bs=msg_bs,
            channel=channel_dict[channel],
            unique_id=unique_id,
            utc_hhmm=utc_hhmm,
            start_slot=start_slot,
            priority=priority)

        # Send the sentences through the IEC 61162-450 processing
        iec_messages = self.iec_61162_450_mg.generate_msg(sentences)

        # Send the IEC 61162-450 Messages via UDP to the VDES1000
        for msg in iec_messages:
            self.udp_interface.send_tgtd_iec_msg(msg.string)

    def send_ais_msg_ratdma(
            self,
            msg_bs,
            channel):
        """
        Send an arbitrary AIS message using RATDMA.

        Issues a VDM sentence.

        Assumes that RATDMA has been enabled for AIS on the VDES1000.

        TODO: Consider adding a query to check if RATDMA is enabled, and if not,
        raise an error.

        Parameters
        ----------
        msg_bs : bitstring.BitStream
            AIS message bitstream, formatted as per Rec. ITU-R M.1371.
        channel : str
            Channel selection ('AIS 1' or 'AIS 2').

        Raises
        ------
        ValueError
            if an unknown channel value is used.

        Returns
        -------
        None.

        """
        channel_dict = {"AIS 1": "A", "AIS 2": "B"}

        if channel not in channel_dict:
            raise ValueError("Unknown channel value.")

        # Encapsulate the message in VDE sentences
        sentences = self.ais_base_sg.generate_vdm(
            msg_bs=msg_bs,
            channel=channel_dict[channel])

        # Send the sentences through the IEC 61162-450 processing
        iec_messages = self.iec_61162_450_mg.generate_msg(sentences)

        # Send the IEC 61162-450 Messages via UDP to the VDES1000
        for msg in iec_messages:
            self.udp_interface.send_tgtd_iec_msg(msg.string)

    def send_ais_binary_broadcast(
            self,
            asm_payload_bs,
            channel,
            msg_id=8):
        """
        Send an AIS binary broadcast message (aka AIS ASM).

        Uses the BBM sentence to send the binary broadcast message as either
        AIS Message Type 8, 14, 25, or 26, depending on the value of msg_id.

        Uses the Source ID (MMSI) stored in the VDES1000's non-volatile memory.

        The VDES1000 FeatureMask bit 0 (AIS) must be enabled when this method
        is used.

        Parameters
        ----------
        asm_payload_bs : bitstring.BitStream
            ASM payload bitstream (the Binary Data portion of the message).
        channel : str
            Channel selection ('no preference', 'AIS 1', 'AIS 2' or 'both').
        msg_id : int, optional
            Message ID as per Rec. ITU-R M.1371:

            - 8: Binary broadcast message;
            - 14: Safety related broadcast message;
            - 25: Single slot binary message;
            - 70: Single slot binary message (unstructured binary data);
            - 26: Multiple slot binary message with Communications State;
            - 71: Multiple slot binary message with Communications State
              (unstructured data).

            The default is 8.

        Raises
        ------
        ValueError
            if an unknown channel value is used.

            if the size of the ASM payload exceeds 68 bytes.

        Returns
        -------
        None.

        """
        channel_dict = {"no preference": 0,
                        "AIS 1": 1,
                        "AIS 2": 2,
                        "both": 3}

        if channel not in channel_dict:
            raise ValueError("Unknown channel value!")

        # Check that the ASM payload won't require more than 3 AIS time
        # slots (the max allowed transmission duration with RATDMA).
        if len(asm_payload_bs) > 68 * 8:
            raise ValueError(
                "The size of the ASM payload must not exceed 68 bytes!")

        # Send the ASM payload through the PL processing
        sentences = self.ais_mob_sg.generate_bbm(
            asm_payload_bs=asm_payload_bs,
            channel=channel_dict[channel],
            msg_id=msg_id)

        # Send the sentences through the IEC 61162-450 processing
        iec_messages = self.iec_61162_450_mg.generate_msg(sentences)

        # Send the IEC 61162-450 Messages via UDP to the VDES1000
        for msg in iec_messages:
            self.udp_interface.send_tgtd_iec_msg(msg.string)

    def send_asm_broadcast(
            self,
            asm_payload_bs,
            source_id,
            channel,
            transmission_format):
        """
        Send a VDES-ASM broadcast message.

        Uses the ABB sentence.

        The VDES1000 FeatureMask bit 2 (ASM) must be enabled when this method
        is used.

        Parameters
        ----------
        asm_payload_bs : bitstring.BitStream
            ASM payload bitstream (the Binary Data portion of the ASM).
        source_id : int
            Source ID (VDES1000 currently only supports 9 digits but should be
            10 digits as per the draft IEC VDES-ASM PAS).
        channel : str
            Channel selection ('no preference', 'ASM 1', 'ASM 2' or 'both').
        transmission_format : int
            Transmission format.

            - 0: No error coding
            - 1: 3/4 FEC
            - 2: ASM SAT uplink message
            - 3-9: Reserved for future use.

        Raises
        ------
        ValueError
            if an unknown channel value is used.

        Returns
        -------
        None.

        """

        channel_dict = {"no preference": 0,
                        "ASM 1": 1,
                        "ASM 2": 2,
                        "both": 3}

        if channel not in channel_dict:
            raise ValueError("Unknown channel value!")

        # Send the ASM payload through the PL processing
        sentences = self.asm_sg.generate_abb(
            asm_payload_bs=asm_payload_bs,
            source_id=source_id,
            channel=channel_dict[channel],
            transmission_format=transmission_format)

        # Send the sentences through the IEC 61162-450 processing
        iec_messages = self.iec_61162_450_mg.generate_msg(sentences)

        # Send the IEC 61162-450 Messages via UDP to the VDES1000
        for msg in iec_messages:
            self.udp_interface.send_tgtd_iec_msg(msg.string)


    def send_vde_data(
            self,
            pi_data_payload_bs,
            destination_id):
        """
        Send data over VDE.

        Uses the VDE Data Message (EDM) sentence.

        The VDES1000 FeatureMask bit TBD (VDE) must be enabled when this method
        is used.

        Parameters
        ----------
        pi_data_payload_bs : bitstring.BitStream
            PI Data Payload bitstream.
        destination_id : int
            Destination ID (VDES1000 currently only supports 9 digits but
            should be 10 digits as per the draft IEC VDES-ASM PAS).

        Returns
        -------
        None.

        """
        # Send the payload down the Presentation Layer
        sentences = self.vde_sg.generate_edm(
            pi_data_payload_bs=pi_data_payload_bs,
            destination_id=destination_id)

        # Send the sentences through the IEC 61162-450 processing
        iec_messages = self.iec_61162_450_mg.generate_msg(sentences)

        # Send the IEC 61162-450 Messages via UDP to the VDES1000
        for msg in iec_messages:
            self.udp_interface.send_tgtd_iec_msg(msg.string)

# =============================================================================
# %% Quick & Dirty Testing
# =============================================================================
if __name__=='__main__':
    from rec_itu_r_m_1371.messages import AISMessage21
    # from iec_61162.part_450.messages import IEC61162450TestMessage

    # VDES1000 Transceiver configuration
    cfg = {"user": {"ip_address": "10.0.1.201",
                    "dest_port_tgtd": 60002,
                    "listen_tgtd": True,
                    "talker_id": "1",
                    "udp_buffer_size": 4096,
                    "udp_verbosity": 3}}

    # Create an AIS Message 21 (AtoN Report)
    ais_msg_21 = AISMessage21(
        source_id=123456789,
        aton_type=30,
        aton_name="Jan's Virtual AtoN",
        pos_accuracy=1,
        lon=1.34,
        lat=51.92,
        dimension=[1,2,3,4],
        epf_device_type=0,
        time_stamp=60,
        off_position=0,
        aton_status=0,
        raim_fl=0,
        vaton_fl=1,
        assigned_mode_fl=0,
        aton_name_extension="")

    vdes_trx = VDESTransceiver(cfg)

    vdes_trx.send_ais_msg(msg_bs=ais_msg_21.bitstream, channel="AIS 1")

    # test_msg = IEC61162450TestMessage(
    #     string="\\g:1-1-47,s:AI01,n:47*49\\!AIBBM,1,1,2,1,8,0@8310,4*1C\r\n")

    # vdes_trx.udp_interface.send_misc_iec_msg(test_msg.string)

    vdes_trx.udp_interface.close()
