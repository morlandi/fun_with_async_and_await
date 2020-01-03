Fun with async and await
========================

Le keywords **async** e **await** recentemente introdotte in Python (3.5 ?)
forniscono un protocollo che ci consente di realizzare programmi asincroni
mediante l'uso di una forma di multitasking collaborativo.

Il componente centrale di questa metodologia e' costituito dalla **coroutine**,
una speciale funzione in grado di sospendere volontariamente la propria esecuzione,
conservando il contesto raggiunto al momento dell'interruzione,
per poter riprendere successivamente l'attività.

.. contents::

.. sectnum::

generators
----------

La possibilità di sospendere momentaneamente l'esecuzione di una routine non è un concetto
totalmente nuovo; già abbiamo incontrato a partire da Python 2.5 ? i **generators**

Esempio:

.. code:: python

    def lazy_range(limit):
        i = 0
        while i < limit:
            yield i
            i += 1
        return

Il termine **generator** indica che questo tipo di funzione non viene invocata
direttamente per eseguire il codice in essa contenuto.

.. code:: python

    In [1]: lazy_range(5)
    Out[1]: <generator object lazy_range at 0x10b432ed0>

Piuttosto, viene utilizzata per creare un **iterator** (o **generator object**),
e da questo ottenere poi l'esecuzione per step successivi mediante l'istruzione **next()**.
Al termine degli step previsti, il completamento delle operazioni viene segnalato
mediante l'eccezione **StopIteration**.

.. code:: python

    In [15]: iterator = lazy_range(3)

    In [16]: next(iterator)
    Out[16]: 0

    In [17]: next(iterator)
    Out[17]: 1

    In [18]: next(iterator)
    Out[18]: 2

    In [19]: next(iterator)
    ---------------------------------------------------------------------------
    StopIteration                             Traceback (most recent call last)
    <ipython-input-19-4ce711c44abc> in <module>
    ----> 1 next(iterator)

    StopIteration:

Il ciclo **for** riconosce e utilizza questo tipo di iterazione:

.. code:: python

    In [20]: iterator = lazy_range(3)

    In [21]: for i in iterator:
        ...:     print(i)
        ...:
    0
    1
    2

Nota: Un comportamento analogo può essere ottenuto più semplicemente senza l'uso di
**generators**, costruendo una sequenza di interi; lo svantaggio, per valori di *limit*
elevati, è l'occupazione di memoria.

Comunicazione bidirezionale con il generator
--------------------------------------------

Come visto nell'esempio precedente, l'argomento di **yield** è il valore ritornato
dal *generator* (o più precisamente dall' *iterator* da esso ricavato) al
chiamante (il codice che ha eseguito *next()*).

Esiste un modo alternativo **iterator.send(data)** per invocare i successivi step
dell' *iterator*, e contemporaneamente inviare ad esso (e quindi nella direzione opposta)
un valore.

Esempio:

.. code:: python

    def lazy_range(limit):
        i = 0
        while i < limit:
            value = yield i
            step = 1 if value is None else value
            i += step
        return

e quindi:

.. code:: python

    In [7]: iterator.send(None)
    Out[7]: 0

    In [8]: iterator.send(None)
    Out[8]: 1

    In [9]: iterator.send(7)
    Out[9]: 8

    In [10]: iterator.send(1)
    Out[10]: 9

    In [11]: iterator.send(1)
    ---------------------------------------------------------------------------
    StopIteration                             Traceback (most recent call last)
    <ipython-input-11-28d2bdbc221e> in <module>
    ----> 1 iterator.send(1)

Il primo utilizzo di send() richiede come unico valore possibile None, per "raggiungere"
l'istruzione **yield**; successivamente il valore passato viene ricevuto dall'iterator,
che lo utilizza, in questo caso, per ridefinire opzionalmente il valore dell'incremento (step).


Una semplice coroutine
----------------------

Proviamo ad utilizzare l'istruzione **async def** per definire una *coroutine*:

.. code:: python

    In [1]: async def bar():
       ...:     print("bar")
       ...:

A differenza di una normale funzione, invocandola non viene eseguito il codice
in essa contenuta, ma piuttosto viene restituito un **coroutine object**:

.. code:: python

    In [2]: bar()
    Out[2]: <coroutine object bar at 0x10b3aa148>

Le analogie con il *generator* sono evidenti; tant'è che possiamo utilizzare
**send()** per procedere con l'esecuzione del codice contenuto in *bar()*:

.. code:: python

    In [3]: coro = bar()

    In [4]: coro
    Out[4]: <coroutine object bar at 0x10b3ec5c8>

    In [5]: coro.send(None)
    bar
    ---------------------------------------------------------------------------
    StopIteration                             Traceback (most recent call last)
    <ipython-input-5-9cc02a983a52> in <module>
    ----> 1 coro.send(None)

    StopIteration:

Siamo molto vicini ad ottenere quanto promesso dal costrutto *coroutine*, e
cioé la possibilità di eseguire il suo codice e definire un punto in cui
sospenderla, in attesa di un opportuno segnale "esterno".

L'ultimo elemente che manca è un **awaitable**, cioé una classe che definisce
un metodo *__await__* in cui eseguirà il *yield* di qualche valore; questo
oggetto sarà l'argomento dell'istruzione sospensiva **await**:

.. code:: python

    In [1]: class Foo():
       ...:
       ...:     def __await__(self):
       ...:         yield "hello"
       ...:

    In [2]: async def bar():
       ...:     print("bar")
       ...:     await Foo()
       ...:

    In [3]: coro = bar()

    In [4]: coro
    Out[4]: <coroutine object bar at 0x109ba6848>

    In [5]: coro.send(None)
    bar
    Out[5]: 'hello'


Un semplice web service sincrono
--------------------------------

Il seguente codice, presentato da **Jonas Obrist** a **PyCon Italy 2019** durante il suo
interessantissimo talk **Artisanal Async Adventures**, realizza un web service
che accetta un valore numerico da clients TCP remoti e invia ad essi il valore
raddoppiato:

file `server.py`:

.. code:: python

    import socket


    def algorithm(n):
        return n * 2


    def handler(sock):
        while True:
            data = sock.recv(100)
            if not data.strip():
                sock.close()
                break
            n = int(data)
            result = algorithm(n)
            sock.send(f'{result}\n'.encode('ascii'))


    def server(address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(address)
        sock.listen(5)
        while True:
            client, addr = sock.accept()
            print(f'Got a connection from {addr}')
            handler(client)


    server(('127.0.0.1',9000))


La funzione **server()** apre un socket TCP sulla porta 9000, e accetta sino
a un massimo di 5 connessioni contemporanee; quanto un nuovo client si connette,
inizia un loop di ricezione (**handler()**) per fornire il servizio richiesto.

Purtroppo la natura sincrona di questo loop di ricezione monopolizza l'attenzione
del server, e nuovi client dovranno attendere il proprio turno.

[![sync web server](etc/screenshots/server.png)](https://vimeo.com/355997908 "sync web server")

Prima di affrontare le modifiche necessarie per renderlo asincrono, al fine di gestire contemporaneamente
la comunicazione con diversi clients, arricchiamo il codice con istruzioni di log
per evidenziare la successione degli eventi:

file `sync_server.py`:

.. code:: python

    import socket
    import signal
    import sys
    import logging


    logger = logging.getLogger(__name__)


    def signal_handler(signal, frame):
        sys.exit(0)


    def set_logger():
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        #handler.setLevel(logging.INFO)
        format = logging.Formatter('%(asctime)s:%(levelname)-8s:%(message)s')
        handler.setFormatter(format)
        logger.addHandler(handler)


    def algorithm(n):
        return n * 2


    def handle(sock):
        while True:
            try:
                data = sock.recv(100)
                if not data.strip():
                    logger.info(f'Closing socket {sock}')
                    sock.close()
                    break
                logger.debug('data: %s', data)
                n = int(data)
                result = algorithm(n)
                logger.info(f'Sending {result} to client')
                sock.send(f'{result}\n'.encode('ascii'))
            except Exception as e:
                sock.send('ERROR\n'.encode('ascii'))
                logger.exception(e)


    def server(host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port, ))
            sock.listen(5)
            logger.info('Server waiting for connections on %s ...', sock)
            while True:
                client, addr = sock.accept()
                logger.info('Connected by %s', addr)
                handle(client)
                logger.info('Connection closed')


    def main():
        signal.signal(signal.SIGINT, signal_handler)
        set_logger()
        server('127.0.0.1', 9000)


    if __name__== "__main__":
      main()


[![sync server with log](etc/screenshots/sync_server.png)](https://vimeo.com/356000169 "sync server with log")


Un web service asincrono
------------------------

Seguendo quanto proposto dal talk di **Jonas Obrist** già citato, trasformeremo
il codice precedente in un servizio asincrono, utilizzando le keywords **async**
e **await** ma non il modulo **asyncio** che fornisce un metodo "nativo" per
realizzare il multitasking collaborativo.

Questo al solo scopo di comprendere i meccanismi sottostanti.

Tuttavia non posso nascondere qualche perplessità sul futuro di **asyncio**;
ho notato infatti che nelle recenti versioni di Python 3.x sono state apportate
modifiche considerevoli al modulo **asyncio**, e diversi costrutti sintattici
sono già stati deprecati (e verranno rimossi nella versione 3.10).

Questo è indicativo del fatto che anche l'attuale implementazione di **asyncio**
potrebbe non essere quella definitiva, e ci dobbiamo probabilmente aspettare evoluzioni
anche significative.

Non a caso, esistono già progetti alternativi che sfruttano le nuove keywords
**await** e **async**, e la disponibilità delle *coroutines*, per proporre soluzioni
indipendenti da **asyncio**; per esempio, per citarne un paio che stanno
riscuotendo un notevole interesse da parte della community:

    - `Trio – a friendly Python library for async concurrency and I/O <https://github.com/python-trio/trio>`_
    - `curio - concurrent I/O <https://github.com/dabeaz/curio>`_

In generale, la soluzione nativa è spesso preferibile; tuttavia non sarebbe il
primo caso in cui l'impostazione *nativa* è servita più per sperimentare nuovi
orizzonti che per garantire la soluzione finale;
cito a titolo d'esempio **urllib2** che spesso e volentieri viene ignorata in
favore di **requests** da molti programmers.


See file `async_server.py <./async_server.py>`_

TODO: explain


Quando e perchè utilizzare asyncio
----------------------------------

Il seguente snippets è un "hello world" per HTTP: esegue un'istruzione GET per
ricevere una pagina HTML remota via HTTP:

.. code:: python

    import requests

    def hello():
        return requests.get("http://httpbin.org/get")

    print(hello())

La soluzione asincrona per ottenere lo stesso risultato, sfruttando **asyncio**
e **aiohttp**, è questa:

.. code:: python

    #!/usr/local/bin/python3.5
    import asyncio
    from aiohttp import ClientSession

    async def hello(url):
        async with ClientSession() as session:
            async with session.get(url) as response:
                response = await response.read()
                print(response)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(hello("http://httpbin.org/headers"))

Tanta roba !

Cosa possiamo concludere ?

1) in termine di leggibilità e semplicità del codice, la soluzione asincrona
   è piuttosto discutibile

2) quanto meno, vorremmo ottenere vantaggi importanti in termine di performances,
   e nel caso precedente non succede

Uno use case che illustra un caso in cui la soluzione asincrona è giusticata e
preferibile è il seguente:

.. code:: python

    base_url = "http://localhost:8080/{}"
    urls = [base_url.format(i) for i in range(5)]

    for url in urls:
        print(requests.get(url).text)

In questo caso, eseguiamo in sequenza 5 GET consecutivi, e il tempo complessivo
sarà la somma del tempo richiesto da ciascuna operazione.

Con una soluzione asincrona, i downloads avvengono in parallelo, e il tempo complessivo
sarà sostanzialmente pari a quello della richiesta più lenta.

.. code:: python

    #!/usr/local/bin/python3.5
    import asyncio
    from aiohttp import ClientSession

    async def fetch(url, session):
        async with session.get(url) as response:
            return await response.read()

    async def run(r):
        url = "http://localhost:8080/{}"
        tasks = []

        # Fetch all responses within one Client session,
        # keep connection alive for all requests.
        async with ClientSession() as session:
            for i in range(r):
                task = asyncio.ensure_future(fetch(url.format(i), session))
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            # you now have all response bodies in this variable
            print(responses)

    def print_responses(result):
        print(result)

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(run(4))
    loop.run_until_complete(future)

Source: `Making 1 million requests with python-aiohttp <https://pawelmhm.github.io/asyncio/python/aiohttp/2016/04/22/asyncio-aiohttp.html>`_


References
----------

- `Jonas Obrist: Artisanal Async Adventures (PyCon Italy 2019) <https://www.youtube.com/watch?v=dTKntbaoYOc>`_
- `Making 1 million requests with python-aiohttp <https://pawelmhm.github.io/asyncio/python/aiohttp/2016/04/22/asyncio-aiohttp.html>`_
- `How the heck does async/await work in Python 3.5? <https://snarky.ca/how-the-heck-does-async-await-work-in-python-3-5/>`_
- `I'm not feeling the async pressure <https://lucumr.pocoo.org/2020/1/1/async-pressure/>`_

