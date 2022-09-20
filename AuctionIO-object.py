#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By: Cezary Bujak
# Created Date: 05-06-2022
# Python version ='3.9'
# ---------------------------------------------------------------------------
"""
AuctionIO is a program that simulates a client-host relationship.
Hosts are working concurrently to each other and to the main root of the app.
The selection of a client that can send its file to a free host is controlled by an equation:
coefficient = (1/c)*t + log_{1/2}(v/c)
Where:
c - number of clients in queue
t - time that client spend in queue
v - volume of the file client want to upload
Based on the coefficient, clients are selected that can send a file to the host at the same
time it must be the smallest file in the file pack.
"""

import datetime
import math
import random
import sys
import time
import tkinter as tk
from threading import Thread
from tkinter import ttk


class AuctionIO(tk.Tk):
    """
        A class that is the main construct of the application, inheriting from the main tkinter module class.

        ...

        Attributes
        ----------
        num_clients : int
            Stores the number of currently waiting clients.
        id : int
            Stores current index which can be assigned to the new client.
        clock_tick : int
            Stores the interval between each tick of the program (in milliseconds).
        clients_list : list
            Stores the information about each client waiting for the file uploading.
        status_list : list
            Stores information about each progress bar (considered as host).

        Methods
        -------
        insert_new_client(self)
            Adds client to the queue. Client appears on table and is stored in clients_list attribute.
        step_proc_pb(self, pb, pb_lab, status_index, name_label)
            Imitates the progress of uploading file into host.
            Responsible for visualizing the movement of the progress bar.
        change_clock_tick(self, component)
            Changes the interval between ticks of the app.
        update(self)
            Recursive. Refreshes whole app, calculates new coefficient's and updates clients statuses, starts new
            threads.
        """

    def __init__(self):
        super().__init__()

        # Configure basic options
        self.title('AuctionIO')
        self.iconbitmap('Logo.ico')
        self.tk.call("source", "sun-valley.tcl")
        self.tk.call("set_theme", "dark")
        self.resizable(False, False)

        # Set up the attributes
        self.num_clients = 0
        self.id = 1
        self.clock_tick = 1000
        self.clients_list = []

        # Set the frames of app
        ttk.LabelFrame(self, name="upper_frame", text="Hosts", padding=5).grid(row=0, column=0)
        ttk.LabelFrame(self, name="scorecard_frame", text="Number of clients").grid(row=0, column=1)

        ttk.Label(self.nametowidget("scorecard_frame"), name="scorecard", text=self.num_clients).pack()
        ttk.Label(self.nametowidget("scorecard_frame"), name="lab").pack()

        ttk.Frame(self, name="bottom_frame", padding=5).grid(row=1, columnspan=2)
        ttk.LabelFrame(self.nametowidget("bottom_frame"), name="table_frame",
                       text="Clients table").grid(row=0, column=0)

        ttk.LabelFrame(self.nametowidget("bottom_frame"), name="buttons_frame", text="Options").grid(row=0, column=1)

        # Configure the upper frame of the application: add the progress bars and labels below them (5 made in for loop)
        for i in range(0, 5):
            ttk.Progressbar(self.nametowidget("upper_frame"), name="pb_" + str(i + 1),
                            orient=tk.VERTICAL, length=40, mode='determinate').grid(row=0, column=i, padx=50, pady=50)
            ttk.Label(self.nametowidget("upper_frame"),
                      text="Host #" + str(i + 1)).grid(row=0, column=i, pady=20, sticky=tk.N)
            ttk.Label(self.nametowidget("upper_frame"), name="pb_lab_" + str(i + 1),
                      text="0%").grid(row=0, column=i, pady=20, sticky=tk.S)

        # Set up the list containing information about status of each of the progress bar.
        # First object in each nested list is the progress bar, second object is label of the progress bar,
        # third object is boolean informing about the activity status of the progress bar. If True, then it is active,
        # if false then it is not active.
        self.status_list = [[self.nametowidget("upper_frame.pb_" + str(i)),
                             self.nametowidget("upper_frame.pb_lab_" + str(i)), False] for i in range(1, 6)]

        # Create main table. Here all data about clients will be displayed.
        ttk.Treeview(self.nametowidget("bottom_frame.table_frame"), name="table", columns=(1, 2, 3, 4),
                     show="headings", height=8).pack(expand=True, fill="both", side='left')
        # Add column names
        for i, text in enumerate(["Id", "File_size", "Time", "Coefficient"]):
            self.nametowidget("bottom_frame.table_frame.table").heading(i + 1, text=text)

        # Add scrollbar to the table.
        ttk.Scrollbar(self.nametowidget("bottom_frame.table_frame"), name="scrollbar",
                      orient=tk.VERTICAL).pack(side=tk.RIGHT, fill=tk.Y)

        # Configure table and scrollbar. Pass scrollbar as the parameter of the table and vice versa.
        self.nametowidget("bottom_frame.table_frame.table"). \
            config(yscrollcommand=self.nametowidget("bottom_frame.table_frame.scrollbar").set)
        self.nametowidget("bottom_frame.table_frame.scrollbar"). \
            config(command=self.nametowidget("bottom_frame.table_frame.table").yview)

        # Set up the buttons
        # Generate user
        ttk.Button(
            self.nametowidget("bottom_frame.buttons_frame"),
            text='Generate client',
            command=lambda: self.insert_new_client(),
        ).grid(row=1, column=0, padx=50, pady=10)

        # Speed up
        ttk.Button(
            self.nametowidget("bottom_frame.buttons_frame"),
            text='Speed up',
            command=lambda: self.change_clock_tick(-100),
        ).grid(row=2, column=0, padx=50, pady=10)

        # Slow down
        ttk.Button(
            self.nametowidget("bottom_frame.buttons_frame"),
            text='Slow down',
            command=lambda: self.change_clock_tick(100),
        ).grid(row=3, column=0, padx=50, pady=10)

        # Start running the in-application time
        self.update()

    def insert_new_client(self):
        """ Inserts new client to the table.
        """

        # Raise the number of clients and refresh the scorecard.
        self.num_clients += 1
        self.nametowidget("scorecard_frame.scorecard").config(text=self.num_clients)
        # Choose randomly the number of files and its size that client will have to upload.
        files = [random.randint(1, 1000) for _ in range(1, random.randint(2, 11))]
        # Sort files from lowest to highest by size of file.
        files.sort()
        # Calculating the coefficient for client. 0 in equation means that the time hasn't started yet.
        coefficient = ((1 / self.num_clients) * 0) + (math.log((files[0] / self.num_clients), 1 / 2))
        # Add new client to the list (for further update of table)
        self.clients_list.append([self.id, files, 0, coefficient])
        # Update id for the next client.
        self.id += 1

    def step_proc_pb(self, pb, pb_lab, status_index, name_label):
        """ Responsible for the illusion of loading a file, handles the movement of
        the progress bar and the update of the labels underneath it.

            Parameters
            ----------
            pb : ttk.Progressbar
                Object of Progressbar class.
            pb_lab : ttk.Label
                Label under progressbar which indicates the status in which progressbar is (in percent).
            status_index : int
                Index of Progressbar located in the list.
            name_label : str
                Label corresponds to client id, information which client file is actually loading.
        """

        # Set status of host (progress bar) as active to inform that it is already in use.
        self.status_list[status_index][2] = True
        # For the range from 1 to 100, for each iteration (0,05 sec * (length of one tick in app/1000))
        # update the progress bar by 1.
        for i in range(1, 101, 1):
            pb['value'] = i
            self.update_idletasks()
            pb_lab.config(text=str(i) + "%" + "\nClient id: " + str(name_label))
            time.sleep(0.05 * (self.clock_tick / 1000))
        pb["value"] = 0
        pb_lab.config(text="0%")
        self.status_list[status_index][2] = False

    def change_clock_tick(self, component):
        """ Changes the value of the clock tick.

                Parameters
                ----------
                component : int
                    Information by what value the clock tick should change.
                """

        self.clock_tick += component
        if self.clock_tick <= 100:
            self.clock_tick = 100

    def update(self):
        """ Update whole app each clock tick.
        """

        # Refresh the time visible under scorecard
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.nametowidget("scorecard_frame.lab"). \
            config(text="Time: {0} Speed: {1} Hz".format(current_time, round(1000 / self.clock_tick, 2)))

        # For each client in the table refresh the time of waiting and calculate new coefficient.
        for i in range(len(self.clients_list)):
            new_time = int(self.clients_list[i][2]) + 1
            new_coefficient = ((1 / self.num_clients) * new_time) + (
                math.log((int(self.clients_list[i][1][0]) / self.num_clients), 1 / 2))
            self.clients_list[i] = [self.clients_list[i][0], self.clients_list[i][1], new_time, new_coefficient]

        # Choose maximum available coefficient
        max_coefficient = 0
        if self.clients_list:
            max_coefficient = self.clients_list[
                [float(i[3]) for i in self.clients_list].index(max([float(i[3]) for i in self.clients_list]))]

        # If coefficient exist, search for available host (progressbar).
        if max_coefficient:
            for i in range(len(self.status_list)):
                if self.status_list[i][2] is False:
                    # Start the thread, delete first file of the client
                    Thread(target=lambda: self.step_proc_pb(self.status_list[i][0],
                                                            self.status_list[i][1], i,
                                                            max_coefficient[0]), daemon=True).start()
                    del self.clients_list[self.clients_list.index(max_coefficient)][1][0]
                    # Check if client has no more files, if yes, then delete the client from list of clients.
                    if not len(self.clients_list[self.clients_list.index(max_coefficient)][1]):
                        self.num_clients -= 1
                        self.nametowidget("scorecard_frame.scorecard").config(text=self.num_clients)
                        del self.clients_list[self.clients_list.index(max_coefficient)]
                    break

        # Update the table based on list of clients.
        self.nametowidget("bottom_frame.table_frame.table"). \
            delete(*self.nametowidget("bottom_frame.table_frame.table").get_children())
        for i in range(len(self.clients_list)):
            self.nametowidget("bottom_frame.table_frame.table"). \
                insert(parent='', index=self.clients_list[i][0],
                       iid=self.clients_list[i][0], values=self.clients_list[i])

        # Run function itself again after self.clock_tick time.
        self.after(self.clock_tick, self.update)


if __name__ == "__main__":
    app = AuctionIO()
    app.mainloop()

    # Shutdown every Thread on app close.
    app.protocol("WM_DELETE_WINDOW", sys.exit())
