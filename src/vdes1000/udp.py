# -*- coding: utf-8 -*-
"""
UDP Interface Module.

This module provides a class designed to manage communications
with the VDES1000 transceiver over UDP.

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
import socket
import struct
from threading import Thread
from vdes1000.utils import ts_print as print

# =============================================================================
# %% Function Definitions
# =============================================================================


# =============================================================================
# %% Class Definitions
# =============================================================================
class UDPInterface():
    """
    A class to manage UDP communications with a VDES1000 unit.

    Parameters
    ----------
    ip_address : str
        IP address of the VDES1000.
    ip_address_tgtd : str
        IP address for the TGTD UDP multicast group. The default is
        "239.192.0.2".
    dest_port_tgtd : int
        Destination port for the TGTD UDP multicast group. The default is
        60002.
    listen_tgtd : bool, optional
        Listen on dest_port_tgtd if True. The default is True.
    recv_cbk_tgtd : function, optional
        Receive event callback function for dest_port_tgtd.

        Expected arguments:

        address : tuple, (ip_address, port)
            Source address.
        data : str
            Received data.

        The default is None.
    buffer_size : int, optional
        Size of the UDP receiving buffer (bytes). The default is 4096.
    verbosity : int, optional
        Verbosity for the UDP interface (0-3) - set > 0 for debugging.
        The default is 0.

    """
    def __init__(
            self,
            ip_address,
            ip_address_tgtd="239.192.0.2",
            dest_port_tgtd=60002,
            listen_tgtd=True,
            recv_cbk_tgtd=None,
            buffer_size=4096,
            verbosity=0):

        # Initialise attributes
        self.ip_address = ip_address
        self.ip_address_tgtd = ip_address_tgtd
        self.dest_port_tgtd = dest_port_tgtd
        self.listen_tgtd = listen_tgtd
        self.buffer_size = buffer_size
        self.verbosity=verbosity

        # Create a UDP socket for sending data to the VDES1000
        self.udp_send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Start threads for receiving data via UDP (one thread per port)
        if any([listen_tgtd]):
            self.run_recv = True
        else:
            self.run_recv = False

        self.threads = []

        if listen_tgtd is True:
            t = Thread(
                target=self.recv,
                args=(self.ip_address_tgtd,self.dest_port_tgtd,recv_cbk_tgtd))
            t.start()
            self.threads.append(t)

        # if listen_aist is True:
        #     t = Thread(
        #         target=self.recv,
        #         args=(self.dest_port_aist,recv_cbk_aist))
        #     t.start()
        #     self.threads.append(t)

    @property
    def n_listening_ports(self):
        """
        Returns
        -------
        int
            Total number of ports the user wishes to listen to.

        """
        return sum([self.listen_tgtd])

    @property
    def n_rx_threads(self):
        """
        Returns
        -------
        int
            Number of currently active receiving threds.

        """
        return len(self.threads)

    def send_tgtd_iec_msg(self, msg_str):
        """
        Send an IEC 61162-450 message to the TGTD port.

        Message is sent to the ip_address and dest_port_tgtd specified during
        the initialisation of the interface object.

        Prints debugging output if self.verbosity > 0.

        Parameters
        ----------
        msg_str : str
            IEC 61162-450 message string.

        Returns
        -------
        None.

        """
        # Send the IEC message to its desitnation via UDP, use UTF-8 encoding
        self.udp_send_sock.sendto(
            msg_str.encode(),
            (self.ip_address, self.dest_port_tgtd))
        # if self.verbosity > 1:
        #     print(
        #         "\nData sent to {:s}:{:d}:".format(
        #             self.ip_address, self.dest_port_misc))
        # if self.verbosity > 2:
        #     print(repr(msg_str), flush=True)
        if self.verbosity > 1:
            print_str = (
                "\nData sent to {:s}:{:d}".format(
                    self.ip_address, self.dest_port_tgtd))
        if self.verbosity > 2:
            print_str += (":\n" + repr(msg_str))

        print(print_str, flush=True)


    def recv(self, ip_address, port, recv_cbk):
        """
        Receive data from a UDP multicast group.

        Prints debugging output if self.verbosity > 0.

        Parameters
        ----------
        ip_address : str
            IP address of the multicast group.
        port : int
            UDP port to listen on.
        recv_cbk : function
            Receive event callback function.

            Expected arguments:

            address : tuple, (ip_address, port)
                Source address.
            data : str
                Received data.

        Returns
        -------
        None.

        """
        if self.verbosity > 0:
            print("Listening to traffic on UDP port {:d} ... ".format(port),
                  flush=True)

        # Create a UDP socket for receiving data
        udp_recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set a timeout for the receive operation
        udp_recv_sock.settimeout(5)

        # Allow multiple sockets to use the same address/port
        udp_recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind the socket to the specified port
        udp_recv_sock.bind(("", port))  # Empty string binds to all interfaces
        # Apparently this is not possible, so have to use different ports on
        # different VDES units.
        # udp_recv_sock.bind((self.ip_address, port))
        # TODO: Test this again with actual VDES1000 hardware:

        # Join the multicast group - tell the operating system to add the socket
        # to the multicast group on all interfaces
        group = socket.inet_aton(self.ip_address_tgtd)
        mreq = struct.pack("4sL", group, socket.INADDR_ANY)
        udp_recv_sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            mreq)

        while self.run_recv:
            try:
                data, address = udp_recv_sock.recvfrom(self.buffer_size)
            except socket.error as err:
                if isinstance(err, socket.timeout):
                    pass
                else:
                    if self.verbosity > 0:
                        print(err)
                    break
            else:
                # if self.verbosity > 1:
                #     print("\nData received from {:s}:{:d}: ".format(
                #         address[0],
                #         address[1]),
                #         flush=True)
                # if self.verbosity > 2:
                #     print(data, flush=True)
                if self.verbosity > 1:
                    print_str = ("\nData received from {:s}:{:d}".format(
                        address[0],
                        address[1]))
                if self.verbosity > 2:
                    # TODO: Check that this is the correct way to decode data
                    print_str += (":\n" + data.decode("utf-8"))

                print(print_str, flush=True)

                # Call the receive callback function and pass the source
                # address (and port) and received data.
                if recv_cbk is not None:
                    recv_cbk(address, data)

        # Tidy up
        udp_recv_sock.close()

        if self.verbosity > 0:
            print("UDP socket for port {:d} closed. ".format(port),
                  flush=True)

    def close(self):
        """
        Close all UDP sockets and stop the receiving threads.

        Failing to call this method before the programme exits may result in
        the receiving threads continuing to run, preventing the respective UDP
        ports from being reused.

        Returns
        -------
        None.

        """
        self.udp_send_sock.close()

        # Interrupts the receiving loops and consequently closes/stops the
        # corresponding sockets and threads.
        self.run_recv = False

        for t in self.threads:
            t.join(6)

# =============================================================================
# %% Quick & Dirty Testing
# =============================================================================
