# -*- coding: utf-8 -*-
"""
UDP Interface for the VDES1000 Transceiver.

Created on Wed Oct 27 11:15:36 2021

@author: Jan Safar
"""

# =============================================================================
# %% Import Statements
# =============================================================================
import socket
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
    dest_port_misc : int
        Destination UDP port for miscelaneous sentences.
    dest_port_aist : int
        Destination UDP port for AIS target data sentences.
    dest_port_ccrd : int
        Destination UDP port for command and command response sentences.
    listen_misc : bool, optional
        Listen on dest_port_misc if True. The default is True.
    listen_aist : bool, optional
        Listen on dest_port_aist if True. The default is True.
    listen_ccrd : TYPE, optional
        Listen on dest_port_ccrd if True. The default is True.
    recv_cbk_misc : function, optional
        Receive event callback function for dest_port_misc.

        Expected arguments:

        address : tuple, (ip_address, port)
            Source address.
        data : str
            Received data.

        The default is None.
    recv_cbk_aist : function, optional
        Receive event callback function for dest_port_aist.
        See also recv_cbk_misc.
        The default is None.
    recv_cbk_ccrd : function, optional
        Receive event callback function for dest_port_ccrd.
        See also recv_cbk_misc.
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
            dest_port_misc,
            dest_port_aist,
            dest_port_ccrd,
            listen_misc=True,
            listen_aist=True,
            listen_ccrd=True,
            recv_cbk_misc=None,
            recv_cbk_aist=None,
            recv_cbk_ccrd=None,
            buffer_size=4096,
            verbosity=0):

        # Initialise attributes
        self.ip_address = ip_address
        self.dest_port_misc = dest_port_misc
        self.dest_port_aist = dest_port_aist
        self.dest_port_ccrd = dest_port_ccrd
        self.listen_misc = listen_misc
        self.listen_aist = listen_aist
        self.listen_ccrd = listen_ccrd
        self.buffer_size = buffer_size
        self.verbosity=verbosity

        # Create a UDP socket for sending data to the VDES1000
        self.udp_send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Start threads for receiving data via UDP (one thread per port)
        # TODO: Add a thread for dest_port_ccrd
        if any([listen_misc, listen_aist, listen_ccrd]):
            self.run_recv = True
        else:
            self.run_recv = False

        self.threads = []

        if listen_misc is True:
            t = Thread(
                target=self.recv,
                args=(self.dest_port_misc,recv_cbk_misc))
            t.start()
            self.threads.append(t)

        if listen_aist is True:
            t = Thread(
                target=self.recv,
                args=(self.dest_port_aist,recv_cbk_aist))
            t.start()
            self.threads.append(t)

    @property
    def n_listening_ports(self):
        """
        Returns
        -------
        int
            Total number of ports the user wishes to listen to.

        """
        return sum([self.listen_misc, self.listen_aist, self.listen_ccrd])

    @property
    def n_rx_threads(self):
        """
        Returns
        -------
        int
            Number of currently active receiving threds.

        """
        return len(self.threads)

    def send_misc_iec_msg(self, msg_str):
        """
        Send an IEC 61162-450 message carrying a 'miscelaneous' sentence.

        Message is sent to the ip_address and dest_port_misc specified during
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
            (self.ip_address, self.dest_port_misc))
        # if self.verbosity > 1:
        #     print(
        #         "\nData sent to {:s}:{:d}:".format(
        #             self.ip_address, self.dest_port_misc))
        # if self.verbosity > 2:
        #     print(repr(msg_str), flush=True)
        if self.verbosity > 1:
            print_str = (
                "\nData sent to {:s}:{:d}".format(
                    self.ip_address, self.dest_port_misc))
        if self.verbosity > 2:
            print_str += (":\n" + repr(msg_str))

        print(print_str, flush=True)


    def recv(self, port, recv_cbk):
        """
        Receive data on a specified UDP port.

        Prints debugging output if self.verbosity > 0.

        Parameters
        ----------
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

        udp_recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        udp_recv_sock.settimeout(5)

        udp_recv_sock.bind(("", port))
        # Apparently this is not possible, so have to use different ports on
        # different VDES units.
        # udp_recv_sock.bind((self.ip_address, port))
        # TODO: Test this again with actual VDES1000 hardware:

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
