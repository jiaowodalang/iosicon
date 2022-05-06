# -*- coding: utf-8 -*

from struct import *
from zlib import *
import stat
import sys
import os

def getNormalizedPNG(filename):
    pngheader = b"\x89PNG\r\n\x1a\n"

    file = open(filename, "rb")
    oldPNG = file.read()
    file.close()
    if oldPNG[:8] != pngheader:
        print(oldPNG[:8])
        return None

    newPNG = oldPNG[:8]

    chunkPos = len(newPNG)

    idatAcc = b""
    breakLoop = False

    # For each chunk in the PNG file    
    while chunkPos < len(oldPNG):
        skip = False

        # Reading chunk
        chunkLength = oldPNG[chunkPos:chunkPos+4]
        chunkLength = unpack(">L", chunkLength)[0]
        chunkType = oldPNG[chunkPos+4 : chunkPos+8]
        #print(chunkType)
        chunkData = oldPNG[chunkPos+8:chunkPos+8+chunkLength]
        chunkCRC = oldPNG[chunkPos+chunkLength+8:chunkPos+chunkLength+12]
        chunkCRC = unpack(">L", chunkCRC)[0]
        chunkPos += chunkLength + 12

        # Parsing the header chunk
        if chunkType == b"IHDR":
            #print(unpack(">L", chunkData[0:4]))
            width = unpack(">L", chunkData[0:4])[0]
            height = unpack(">L", chunkData[4:8])[0]

        # Parsing the image chunk
        if chunkType == b"IDAT":
            # Store the chunk data for later decompression
            #idatAcc = b''
            idatAcc += chunkData
            skip = True

        # Removing CgBI chunk        
        if chunkType == b"CgBI":
            skip = True

        # Add all accumulated IDATA chunks
        if chunkType == b"IEND":
            try:
                # Uncompressing the image chunk
                bufSize = width * height * 4 + height
                #print(len(idatAcc))
                chunkData = decompress( idatAcc, -15, bufSize)
                #print(len(chunkData))

            except Exception as e:
                # The PNG image is normalized
                print(e)
                return None

            chunkType = b"IDAT"

            # Swapping red & blue bytes for each pixel
            newdata = b""
            #print(width)
            #print(height)
            for y in range(height):
                print(len(newdata))
                i = len(newdata)
                if i >=len(chunkData):
                    continue
                #print(bytes([chunkData[i]]))
                newdata += bytes([chunkData[i]])
                for x in range(width):
                    i = len(newdata)
                    newdata += bytes([chunkData[i+2]])
                    newdata += bytes([chunkData[i+1]])
                    newdata += bytes([chunkData[i+0]])
                    newdata += bytes([chunkData[i+3]])

            # Compressing the image chunk
            chunkData = newdata
            chunkData = compress( chunkData )
            chunkLength = len( chunkData )
            chunkCRC = crc32(chunkType)
            chunkCRC = crc32(chunkData, chunkCRC)
            chunkCRC = (chunkCRC + 0x100000000) % 0x100000000
            breakLoop = True

        if not skip:
            newPNG += pack(">L", chunkLength)
            newPNG += chunkType
            if chunkLength > 0:
                newPNG += chunkData
            newPNG += pack(">L", chunkCRC)
        if breakLoop:
            break

    return newPNG

def updatePNG(filename):
    data = getNormalizedPNG(filename)
    print(data)
    if data != None:
        file = open(filename.split('.')[0]+'_new.png', "wb")
        file.write(data)
        file.close()
        return True
    return data

if __name__ == '__main__':
    updatePNG(sys.argv[1])


