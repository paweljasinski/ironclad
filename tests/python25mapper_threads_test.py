
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

from System.Threading import Thread, ThreadStart

from Ironclad import Python25Mapper


class Python25Mapper_PyThread_functions_Test(TestCase):

    def testAllocateAndFreeLocks(self):
        mapper = Python25Mapper()

        lockPtr1 = mapper.PyThread_allocate_lock()
        lockPtr2 = mapper.PyThread_allocate_lock()

        self.assertNotEquals(lockPtr1, lockPtr2, "bad, wrong")

        lockObject1 = mapper.Retrieve(lockPtr1)
        lockObject2 = mapper.Retrieve(lockPtr2)

        self.assertNotEquals(lockObject1, lockObject2, "bad, wrong")

        mapper.PyThread_free_lock(lockPtr1)
        mapper.PyThread_free_lock(lockPtr2)  
        mapper.Dispose()


    def testAcquireAndReleaseLocksWithWait(self):
        mapper = Python25Mapper()

        lockPtr1 = mapper.PyThread_allocate_lock()
        lockPtr2 = mapper.PyThread_allocate_lock()

        self.assertEquals(mapper.PyThread_acquire_lock(lockPtr1, 1), 1, "claimed failure")
        self.assertEquals(mapper.PyThread_acquire_lock(lockPtr2, 1), 1, "claimed failure")

        acquired = set()
        def AcquireLock(ptr):
            self.assertEquals(mapper.PyThread_acquire_lock(ptr, 1), 1, "claimed failure")
            acquired.add(ptr)
            mapper.PyThread_release_lock(ptr)

        t1 = Thread(ThreadStart(lambda: AcquireLock(lockPtr1)))
        t2 = Thread(ThreadStart(lambda: AcquireLock(lockPtr2)))
        t1.Start()
        t2.Start()
        Thread.Sleep(100)

        self.assertEquals(acquired, set(), "not properly locked")

        mapper.PyThread_release_lock(lockPtr1)
        Thread.Sleep(100)
        self.assertEquals(acquired, set([lockPtr1]), "release failed")

        mapper.PyThread_release_lock(lockPtr2)
        Thread.Sleep(100)
        self.assertEquals(acquired, set([lockPtr1, lockPtr2]), "release failed")    
        mapper.Dispose()


    def testAcquireAndReleaseLocksWithNoWait(self):
        mapper = Python25Mapper()

        lockPtr1 = mapper.PyThread_allocate_lock()
        lockPtr2 = mapper.PyThread_allocate_lock()

        self.assertEquals(mapper.PyThread_acquire_lock(lockPtr1, 1), 1, "claimed failure")
        self.assertEquals(mapper.PyThread_acquire_lock(lockPtr2, 1), 1, "claimed failure")

        failedToAcquire = set()
        def FailToAcquireLock(ptr):
            self.assertEquals(mapper.PyThread_acquire_lock(ptr, 0), 0, "claimed success")
            failedToAcquire.add(ptr)

        t1 = Thread(ThreadStart(lambda: FailToAcquireLock(lockPtr1)))
        t2 = Thread(ThreadStart(lambda: FailToAcquireLock(lockPtr2)))
        t1.Start()
        t2.Start()
        Thread.Sleep(100)

        self.assertEquals(failedToAcquire, set([lockPtr1, lockPtr2]), "failed")

        mapper.PyThread_release_lock(lockPtr1)
        mapper.PyThread_release_lock(lockPtr2)

        acquired = set()
        def AcquireLock(ptr):
            self.assertEquals(mapper.PyThread_acquire_lock(ptr, 0), 1, "claimed failure")
            acquired.add(ptr)
            mapper.PyThread_release_lock(ptr)

        t1 = Thread(ThreadStart(lambda: AcquireLock(lockPtr1)))
        t2 = Thread(ThreadStart(lambda: AcquireLock(lockPtr2)))
        t1.Start()
        t2.Start()
        Thread.Sleep(100)

        self.assertEquals(acquired, set([lockPtr1, lockPtr2]), "acquires failed")    
        mapper.Dispose()


suite = makesuite(
    Python25Mapper_PyThread_functions_Test,
)

if __name__ == '__main__':
    run(suite)