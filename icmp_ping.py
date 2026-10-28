from socket import *
import os
import sys
import struct
import time
import select

def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = string[count+1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + string[len(string) - 1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def receive_one_ping(icmpSocket, destinationAddress, ID, timeout):
    timeLeft = timeout
    while True:
        startedSelect = time.time()
        whatReady = select.select([icmpSocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: # Timeout
            return None

        timeReceived = time.time()
        recPacket, addr = icmpSocket.recvfrom(1024)

        icmpHeader = recPacket[20:28]
        type, code, rev_checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

        if packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            return timeReceived - timeSent

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return None

def send_one_ping(icmpSocket, destinationAddress, ID):
    header = struct.pack("bbHHh", 8, 0, 0, ID, 1)
    data = struct.pack("d", time.time())

    myChecksum = checksum(header + data)
    
    header = struct.pack("bbHHh", 8, 0, htons(myChecksum), ID, 1)
    packet = header + data

    icmpSocket.sendto(packet, (destinationAddress, 1)) 

def ping(host, timeout=1):
    icmp = getprotobyname("icmp")
    try:
        icmpSocket = socket(AF_INET, SOCK_RAW, icmp)
    except error as e:
        print(f"Akses ditolak. Jalankan script sebagai Administrator/Root. Error: {e}")
        return

    dest_addr = gethostbyname(host)
    print(f"\nPinging {host} [{dest_addr}] menggunakan Python ICMP Socket:")

    myID = os.getpid() & 0xffff

    for i in range(4):
        try:
            send_one_ping(icmpSocket, dest_addr, myID)
            delay = receive_one_ping(icmpSocket, dest_addr, myID, timeout)
            
            if delay is None:
                print("Request timed out.")
            else:
                delay_ms = delay * 1000
                print(f"Reply from {dest_addr}: bytes=32 time={delay_ms:.2f}ms TTL=64")
        except KeyboardInterrupt:
            print("\nPing dihentikan oleh pengguna.")
            break
        time.sleep(1) 

    icmpSocket.close()

if __name__ == '__main__':
    target = "127.0.0.1" 
    ping(target)