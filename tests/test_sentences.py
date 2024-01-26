# -*- coding: utf-8 -*-
"""
Tests for the Sentences Module.

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
import pytest
from bitstring import BitStream

# Local Modules ---------------------------------------------------------------
from vdes1000.sentences import EDMSentence, SentenceGenerator


# =============================================================================
# %% Test Cases
# =============================================================================
def test_valid_edm_sentence_creation():
    edm_sentence = EDMSentence(
        seq_nr=999,
        source_id=123456789,
        destination_id=987654321,
        data="0101010101",
        n_fill_bits=4)

    assert edm_sentence.seq_nr == 999
    assert edm_sentence.source_id == 123456789
    assert edm_sentence.destination_id == 987654321
    assert edm_sentence.data == "0101010101"
    assert edm_sentence.n_fill_bits == 4
    assert edm_sentence.talker_id == "AI"

@pytest.mark.parametrize("seq_nr", [(-1), (1000)])
def test_invalid_seq_nr_raises_value_error(seq_nr):
    with pytest.raises(ValueError, match="seq_nr must be between 0 and 999!"):
        edm = EDMSentence(
            seq_nr=seq_nr,
            source_id=123456789,
            destination_id=987654321,
            data="0101010101",
            n_fill_bits=4,
            talker_id="AI")

def test_edm_string_generation():
    edm = EDMSentence(
        seq_nr=500,
        source_id=123456789,
        destination_id=987654321,
        data="0101010101",
        n_fill_bits=4,
        talker_id="VD")

    expected_string = "$VDEDM,500,123456789,987654321,0101010101,4*72\r\n"

    assert edm.string == expected_string

def test_sentence_generator_creation():
    sg = SentenceGenerator()

    assert sg.talker_id == "AI"
    assert sg.edm_seq_nr == 0

def test_sentence_generator_generate_edm_valid_payload():
    pi_data_payload_bs = BitStream(664 * 6)

    sg = SentenceGenerator()

    sentence_groups = sg.generate_edm(
        pi_data_payload_bs=pi_data_payload_bs,
        destination_id=987654321)

    assert len(sentence_groups) == 1
    assert len(sentence_groups[0]) == 1
    assert isinstance(sentence_groups[0][0], EDMSentence)
    assert sentence_groups[0][0].n_fill_bits == 0
    assert sentence_groups[0][0].data == "0" * 664

def test_sentence_generator_generate_edm_large_payload_error():
    pi_data_payload_bs = BitStream(664 * 6 + 1)

    sg = SentenceGenerator()

    with pytest.raises(ValueError, match="Size of the PI Data Payload exceeds the currently supported maximum."):
        sg.generate_edm(pi_data_payload_bs, 987654321)


def test_generate_edm_sequence_number_increment():
    pi_data_payload_bs = BitStream("0b0101010101")
    destination_id = 123456789
    sg = SentenceGenerator()

    sg.generate_edm(pi_data_payload_bs, destination_id)
    assert sg.edm_seq_nr == 1

    sg.generate_edm(pi_data_payload_bs, destination_id)
    assert sg.edm_seq_nr == 2

    # Test roll over
    sg.edm_seq_nr = 999

    sg.generate_edm(pi_data_payload_bs, destination_id)
    assert sg.edm_seq_nr == 0


# =============================================================================
# %% Main Function
# =============================================================================
if __name__ == '__main__':
    pytest.main()
