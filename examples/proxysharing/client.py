from __future__ import print_function
import time
import threading
import Pyro4.naming
import Pyro4.core


stop = False


def myThread(nsproxy, proxy):
    global stop
    name = threading.current_thread().name
    try:
        while not stop:
            result = nsproxy.list(prefix="example.")
            result = proxy.method("the quick brown fox jumps over the lazy dog")
    except Exception as x:
        print("**** Exception in thread %s: {%s} %s" % (name, type(x), x))


nsproxy = Pyro4.naming.locateNS()
proxy = Pyro4.core.Proxy("PYRONAME:example.proxysharing")

# now create a handful of threads and give each of them the same two proxy objects
threads = []
for i in range(5):
    thread = threading.Thread(target=myThread, args=(nsproxy, proxy))
    # thread.daemon = True
    thread.daemon = False
    threads.append(thread)
    thread.start()

print("Running a bunch of threads for 5 seconds.")
print("They're hammering the name server and the test server using the same proxy.")
print("You should not see any exceptions.")
time.sleep(5)
stop = True
for thread in threads:
    thread.join()
print("Done.")

print("\nNow showing why proxy sharing might not be a good idea for parallelism.")
print("Starting 10 threads with the same proxy that all call the work() method.")


def myThread2(proxy):
    global stop
    while not stop:
        proxy.work()


stop = False
proxy.reset_work()
threads = []
for i in range(10):
    thread = threading.Thread(target=myThread2, args=[proxy])
    thread.daemon = False
    threads.append(thread)
    thread.start()

print("waiting 5 seconds")
start = time.time()
time.sleep(5)
print("waiting until threads have stopped...")
stop = True
for thread in threads:
    thread.join()
duration = int(time.time() - start)
print("--> time until everything completed: %.2f" % duration)
print("--> work done on the server: %d" % proxy.get_work_done())
print("you can see that the 10 threads are waiting for each other to complete,")
print("and that not a lot of work has been done on the server.")

print("\nDoing the same again but every thread now has its own proxy.")
print("Starting 10 threads with different proxies that all call the work() method.")
proxy.reset_work()
stop = False
threads = []
for i in range(10):
    proxy = Pyro4.core.Proxy(proxy._pyroUri)  # create a new proxy
    thread = threading.Thread(target=myThread2, args=[proxy])
    thread.daemon = False
    threads.append(thread)
    thread.start()

print("waiting 5 seconds")
start = time.time()
time.sleep(5)
print("waiting until threads have stopped...")
stop = True
for thread in threads:
    thread.join()
duration = int(time.time() - start)
print("--> time until everything completed: %.2f" % duration)
print("--> work done on the server: %d" % proxy.get_work_done())
print("you can see that this time the 10 threads didn't have to wait for each other,")
print("and that they got a lot more work done because they really ran in parallel.")
