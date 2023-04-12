# antifragile
pilot project about socket

## requirements
Python3.7 +
> pip install -r requirements.txt

## get started

### server
> python tts.py --port=1234 --ping=5.0 --log-level=info

```
python tts.py --help
Usage: tts.py [OPTIONS]

Options:
  --port INTEGER                  set port (default: 1234)  [required]
  --ping FLOAT                    set interval of ping (default: 0.0 seconds)
  --log-level [debug|info|warn|error|critical]
                                  set log level (default: info)
  --rtls TEXT                     set rtls host:port(default:
                                  192.168.40.254:9999)  [required]

  --joycon                        get status of joycon(left/right)
  --help                          Show this message and exit.

```


> (Deprecated) python echo_server.py --port=1234 --ping=5.0 --log-level=info

```
% python3.7 echo_server.py --help
Usage: echo_server.py [OPTIONS]

Options:
  --port INTEGER                  set port (default: 1234)  [required]
  --ping FLOAT                    set interval of ping (default: 0.0 seconds)
  --log-level [debug|info|warn|error|critical]
                                  set log level (default: info)
  --help                          Show this message and exit.

```

### client
> python echo_client.py --host=localhost --port=1234 --uid=1

> python echo_client.py --uid={n}

```
% python3.7 echo_client.py --help
Usage: echo_client.py [OPTIONS]

Options:
  --host TEXT     set server host  [required]
  --port INTEGER  set server port  [required]
  --uid INTEGER   set uid for player  [required]
  --help          Show this message and exit.

```

## how to flatbuffers class
### Python
> flatc --python antifragile.fbs
### CSharp
> flatc --csharp antifragile.fbs
