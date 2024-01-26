# -*- coding: utf-8 -*-
"""
VDES1000 Sentences Module.

This module contains classes and functions for representing, generating [and
parsing] CML Microcircuits-propietary sentences specified in the VDES1000
datasheet v6, dated January 2023.

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

# Third-party Modules ---------------------------------------------------------
from bitstring import BitStream

# Local Modules ---------------------------------------------------------------
from iec_61162.part_1.sentences import iec_checksum, iec_ascii_6b_to_8b


# =============================================================================
# %% Helper Functions
# =============================================================================


# =============================================================================
# %% Sentence Definitions
# =============================================================================
#### AIS Sentences ------------------------------------------------------------

#### VDES-ASM Sentences -------------------------------------------------------

#### VDE Sentences ------------------------------------------------------------
class EDMSentence:
    """
    EDM Sentence: VDE data message.

    Parameters
    ----------
    seq_nr : int
        Sequence number of PI data session (0-999).
    source_id : int
        Source ID (10 digits as per the draft IEC VDES-ASM PAS; VDES1000
        currently only supports 9 digits). Only applicable when receiving VDE
        data over the RF link. When the EDM sentence is sent to the
        presentation interface, this value is ignored and must be null.
    destination_id : int
        Destination ID (10 digits as per the draft IEC VDES-ASM PAS; VDES1000
        currently only supports 9 digits). Null field implies broadcast.
    data : str
        Encapsulated binary data. May contain a maximum of 498 bytes of data
        (or 664 6-bit characters). The data size is constrained by the payload
        limit of a VDE data session when using the lowest data rate, because
        EDM payload can not currently span multiple VDE data sessions.
    n_fill_bits : int
        Number of fill bits (0-5).
    talker_id : str, optional
        Talker ID. The default is "AI".

    Raises
    ------
    ValueError
        if seq_nr is out of the expected limits.

    """
    formatter_code = "EDM"

    def __init__(
            self,
            seq_nr,
            source_id,
            destination_id,
            data,
            n_fill_bits,
            talker_id="AI"):

        # TODO: Add input checking / setters/getters
        self.seq_nr = seq_nr
        self.source_id = source_id
        self.destination_id = destination_id
        self.data = data
        self.n_fill_bits = n_fill_bits
        self.talker_id = talker_id

    @property
    def seq_nr(self):
        return self._seq_nr

    @seq_nr.setter
    def seq_nr(self, value):
        if 0 <= value <= 999:
            self._seq_nr = value
        else:
            raise ValueError("seq_nr must be between 0 and 999!")

    @property
    def string(self):
        """
        Returns
        -------
        s : str
            Sentence string, formatted as per the VDES1000 Datasheet v.6, 2023.

        """
        s = "${:s}{:s},{:d},{:s},{:s},{:s},{:d}".format(
            self.talker_id,
            self.formatter_code,
            self.seq_nr,
            self.source_id if self.source_id == "" else str(self.source_id),
            self.destination_id if self.destination_id == "" else str(self.destination_id),
            self.data,
            self.n_fill_bits)

        checksum = iec_checksum(s)
        s += "*" + "{:>02X}".format(checksum) + "\r\n"

        return s

#### Other Proprietary Sentences ----------------------------------------------

# =============================================================================
# %% Sentence Generation
# =============================================================================
class SentenceGenerator:
    """
    VDES Sentence Generator.

    Parameters
    ----------
    talker_id : str, optional
        Talker ID. The default is "AI".

    """
    def __init__(self, talker_id="AI"):
        self.talker_id = talker_id
        self.edm_seq_nr = 0

    def generate_edm(
            self,
            pi_data_payload_bs,
            destination_id,
            talker_id="AI"):
        """
        Generate an EDM sentence encapsulating a PI Data Payload bitstream.

        Parameters
        ----------
        pi_data_payload_bs : bitstring.BitStream
            PI Data Payload bitstream. Payload size currently limited by the
            use of the CML-proprietary EDM sentence to 498 bytes (664 chars.).
        destination_id : int
            Destination ID (10 digits as per the draft IEC VDES-ASM PAS; VDES1000
            currently only supports 9 digits). Null field implies broadcast.
        talker_id : str, optional
            Talker ID. The default is "AI".

        Returns
        -------
        list of lists of vdes1000.sentences.EDMSentence
            List of lists of EDM sentences encapsulating the PI Data Payload
            bitstream.

        """
        n_bits = len(pi_data_payload_bs)

        # Pad the payload with fill bits
        n_fill_bits = int((6 - (n_bits % 6)) % 6)
        padded_payload_bs = pi_data_payload_bs + BitStream(n_fill_bits)

        # Encode the payload as a sequence of 8-bit ASCII characters, each
        # corresponding to one 6-bit ASCII character
        pi_data_payload_str = iec_ascii_6b_to_8b(padded_payload_bs)

        # Maximum data size for the EDM sentence. The data size is constrained
        # by the payload limit of a VDE data session when using the lowest data
        # rate, because EDM payload can not currently span multiple VDE data
        # sessions.
        max_edm_data_char = 664

        if len(pi_data_payload_str) > max_edm_data_char:
            raise ValueError("Size of the PI Data Payload exceeds the currently supported maximum.")

        edm_sentence = EDMSentence(
            seq_nr=self.edm_seq_nr,
            source_id="",
            destination_id=destination_id,
            data=pi_data_payload_str,
            n_fill_bits=n_fill_bits,
            talker_id=talker_id)

        # Increase seq_nr and roll over after 999
        self.edm_seq_nr = (self.edm_seq_nr + 1) % 1000

        return [[edm_sentence]]

# =============================================================================
# %% Sentence Parsing
# =============================================================================


# =============================================================================
# %% Quick & Dirty Testing
# =============================================================================
if __name__ == "__main__":

    # Create a sentence
    edm_sentence = EDMSentence(
        # seq_nr=0,
        # source_id="",
        # destination_id=222222222,
        # data="Beam me up Scotty",
        # n_fill_bits=0)
        seq_nr=3,
        source_id=0,
        destination_id=2,
        data="Hallo:World",
        n_fill_bits=2)

    print(edm_sentence.string)


    # Create a PI Data Payload bitstream
    pi_data_payload_bs = BitStream(664*6)

    # Initialise the Sentence Generator
    sg = SentenceGenerator()

    # Generate a sentence
    sentence_groups = sg.generate_edm(
        pi_data_payload_bs=pi_data_payload_bs,
        destination_id=222222222)

    for group in sentence_groups:
        for sentence in group:
            print(sentence.string)
