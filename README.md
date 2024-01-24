# The VDES1000 Python Package

## Description

The VDES1000 Python Package offers convenient high-level interfaces for communication with the [CML Microcircuits VDES1000](https://cmlmicro.com/products/maritime-communications/product/vdes1000-vhf-data-exchange-system-vdes-module) transceiver.

It has been developed using Python v.3.11.1.

## Installation

1. Ensure [Python](https://www.python.org/downloads/) and the [PDM](https://pdm-project.org/) dependency manager are installed.

1. Clone the GRAD `py_vdes1000` repository.
    ```
    git clone https://github.com/jan-safar/py_vdes1000.git
    ```

1. Navigate to the local repository.
    ```
    cd py_vdes1000
    ```

1. Install the VDES1000 package and its dependencies from the `pdm.lock` file.
    ```
    pdm sync --prod
    ```
    After successfully executing the above command, `pdm` will generate a virtual Python environment in `./.venv/` and install the package along with its required dependencies into it in *production mode*.

## Example Applications

Three example applications are included in the `./examples/` directory:

* `minimal_tx.py` demonstrates a minimal VDE transmitter;
* `vdes_tx_app.py` allows the user to send sample AIS, VDES-ASM and VDE transmissions; and
* `vdes_rx_app.py` displays data received over AIS, VDES-ASM or VDE.

### Execution Options

These applications can be executed through various methods:

* Python Integrated Development Environment (IDE):
    1. Point your Python IDE to the interpreter within the virtual environment created during installation.
    2. Run the examples from within your IDE.
* Python on the Command Line:

    1. Activate the virtual environment created during installation (the exact method depends on your operating system).
    2. Use the `python <example_script_name>` command.

* Using `pdm` on the Command Line:
    * `pdm run <example_script_name>`
    * `pdm` will automatically run the script in the corresponding virtual environment.

### Example Execution

For example, to execute `minimal_tx.py` using the last method, issue the following commands at the command prompt:
```
cd examples
pdm run minimal_tx.py
```

Upon execution, the application will open two UDP sockets to listen for incoming traffic from a VDES1000 transceiver. It will then send an EDM sentence to the transceiver, initiating an addressed VDE transmission of a 32-byte payload. Configuration details, such as the IP address, UDP ports and Destination ID (MMSI) are hardcoded in the source file, `minimal_tx.py`.

```
Listening to traffic on UDP port 60030 ... 
Listening to traffic on UDP port 60031 ... 

Data sent to 10.0.2.203:60030:
'\\g:1-1-1,s:1*38\\$AIEDM,0,,992359599,0000000000000000000000000000000000000000000,2*62\r\n'
```

Assuming a VDES1000 transceiver is available at the target IP address and port, a response will be received (an EAK sentence), confirming that the transceiver has queued the data for transmission.

```
Data received from 10.0.2.203:60030:
\g:1-1-92,s:AI01,d:1,n:686*39\$VEEAK,0,992359599,Q*29
```

Another response (an EDO sentence) will be received once the data has been successfully transmitted.

```
Data received from 10.0.2.203:60030:
\g:1-1-93,s:AI01,d:1,n:687*39\!VEEDO,0,992359598,992359599,0000000000000000000000000000000000000000000,2*42
```

If the transmission is successfully received by another VDES1000 transceiver, an acknowledgment will be sent over the VHF Data Link (VDL) back to the initiating transceiver. Once the acknowledgment is successfully received, a final response will be issued.

```
Data received from 10.0.2.203:60030:
\g:1-1-94,s:AI01,d:1,n:688*31\$VEEAK,0,992359599,A*39
```

For details of the other two example applications, `vdes_tx_app` and `vdes_rx_app`, refer to the corresponding source files.

## Code Usage

The main modules of the VDES1000 package are located under `./src/vdes1000/`.

### Module: `trx.py`

This module provides high-level interfaces for initiating AIS, VDES-ASM and VDE transmissions and receiving transceiver responses. It uses IEC-defined Presentation Interface (PI) sentence formatters implemented within the Python packages referenced in the 'Related Projects' section below. These formatters include:

* TSA, 'Transmit slot assignment';
* VDM, 'AIS VHF data-link message';
* BBM, 'AIS binary broadcast message'; and
* ABB, 'ASM broadcast message'.

VDE transmissions are initiated using the CML-Microcircuits-proprietary EDM sentence formatter, implemented in the `sentences.py` module.

Outgoing PI sentences are encapsulated in IEC 61162-450 messages and sent to the transceiver using the UDP protocol.

For examples of usage, see the source code of the example applications introduced above. A minimal example is reproduced below.

```python
# bitstring.BitStream is used throughout to represent data payloads
from bitstring import BitStream
from vdes1000.trx import VDESTransceiver

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

# Create a PI Data Payload to be transmitted
pi_data_payload_bs = BitStream(8 * 32)

# Initiate an addressed data transfer over VDE
vdes_trx.send_vde_data(pi_data_payload_bs, destination_id="992359599")

input("\nPress Enter to exit.")

# Close the UDP sockets when done
vdes_trx.udp_interface.close()
```

### Module: `sentences.py`

This module includes classes and functions for generating and parsing CML Microcircuits-propietary PI sentences specific to the VDES1000 transceiver. Currently, support for the EDM sentence, 'VDE data message' has been implemented.

### Module: `udp.py`

This module provides a class designed to manage UDP communications with the VDES1000 transceiver. It is used by the high-level (`VDESTransceiver`) class defined in the `trx.py` module.

### Module: `utils.py`

This module contains various utility functions and classes.

## Contributing

We welcome contributions! If you wish to contribute to this project, please follow these steps:

1. Fork the repository and create a new branch.
1. Clone your repository to your local machine.
    
    ```
    git clone <your_repository_address>
    cd py_vdes1000
    ```
1. Install the package in *development mode* using PDM.
    ```
    pdm sync --dev
    ```    
    
    Note: The development installation includes dependencies for the [Spyder IDE](https://www.spyder-ide.org/), which may not be necessary if you are using a different IDE.
1. Make your changes and test thoroughly.
1. Submit a pull request with a clear description of your changes.

## Tests

This is currently work in progress. 

Unit test modules are expected to be located in `./tests/`. The chosen testing framework for this project is [pytest](https://pytest.org), included as part of the development installation.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](./LICENSE) file for details.

## Support

Email: Jan.Safar@gla-rad.org

Issue Tracker: [GitHub Issues](https://github.com/jan-safar/py_vdes1000/issues)

## Related Projects

### Python

* [Recommendation ITU-R M.1371 package](https://github.com/jan-safar/py_rec_itu_r_m_1371.git)
* [IEC 61162 package](https://github.com/jan-safar/py_iec_61162.git)
* [IEC 62320 package](https://github.com/jan-safar/py_iec_62320.git)
* [IEC PAS 63343 package](https://github.com/jan-safar/py_iec_pas_63343.git)

### Java

* [VDES1000 Library](https://github.com/gla-rad/VDES1000Lib) - a Java port of this package.
