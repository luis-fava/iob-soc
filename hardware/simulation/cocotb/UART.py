#
# UART Serial class and function that helps the simulation to comunicate with the console

import os

# address macros
UART_SOFTRESET_ADDR = 0
UART_DIV_ADDR = 1
UART_TXDATA_ADDR = 2
UART_TXEN_ADDR = 3
UART_TXREADY_ADDR = 4
UART_RXDATA_ADDR = 5
UART_RXEN_ADDR = 6
UART_RXREADY_ADDR = 7

# other macros
FREQ = 100000000
BAUD = 5000000
CLK_PERIOD = 10 # 20 ns

from cocotb.triggers import Timer, RisingEdge
from cocotb.clock import Clock

CONSOLE_DIR = '../../../software/console/'
# 1-cycle write
async def uartwrite(dut, cpu_address, cpu_data):
    await Timer(1, units="ns")
    dut.uart_addr.value = cpu_address
    dut.uart_valid.value = 1
    dut.uart_wstrb.value = int.from_bytes(b'\x0f', "big")
    dut.uart_wdata.value = cpu_data
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.uart_wstrb.value = 0;
    dut.uart_valid.value = 0;

# 2-cycle read
async def uartread(dut, cpu_address):
    await Timer(1, units="ns")
    dut.uart_addr.value = cpu_address
    dut.uart_valid.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    #print(dut.uart_rdata.value)
    read_reg = dut.uart_rdata.value.integer
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")
    dut.uart_valid.value = 0;
    return read_reg;

async def inituart(dut):
    #pulse reset uart
    await uartwrite(dut, UART_SOFTRESET_ADDR, 1)
    await uartwrite(dut, UART_SOFTRESET_ADDR, 0)
    #config uart div factor
    await uartwrite(dut, UART_DIV_ADDR, int(FREQ/BAUD))
    #enable uart for receiving
    await uartwrite(dut, UART_RXEN_ADDR, 1)
    await uartwrite(dut, UART_TXEN_ADDR, 1)

class UART:
    def __init__(self, dut):
        self.dut = dut

    async def read(self, number_of_bytes = 1):
        i = 0
        data = b''
        while(i<number_of_bytes):
            RXready = 0
            while(RXready != 1):
                RXready = await uartread(self.dut, UART_RXREADY_ADDR)
            char = await uartread(self.dut, UART_RXDATA_ADDR)
            data += chr(char)
            #print('Read: "{0}"'.format(data))
            i += 1
        return data

    async def read_until(self, end = b'\x00'):
        i = 0
        data = b''
        while(True):
            RXready = 0
            while(RXready != 1):
                RXready = await uartread(self.dut, UART_RXREADY_ADDR)
            char = await uartread(self.dut, UART_RXDATA_ADDR)
            data += chr(char)
            #print('Read: "{0}"'.format(data))
            if (data[-1] == end):
                break
        return data

    async def write(self, data):
        send = int.from_bytes(data, "big")
        TXready = 0
        while(TXready != 1):
            TXready = await uartread(self.dut, UART_TXREADY_ADDR)
        await uartwrite(self.dut, UART_TXDATA_ADDR, send)
