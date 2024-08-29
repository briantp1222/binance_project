import numpy as np
import pyopencl as cl
import logging

class GPUProcessing:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.context, self.queue = self.setup_opencl()
        logging.basicConfig(level=logging.DEBUG)

    def setup_opencl(self):
        platform = cl.get_platforms()[0]
        device = platform.get_devices()[0]
        context = cl.Context([device])
        queue = cl.CommandQueue(context)
        return context, queue

    def parallel_process(self, data):
        logging.info("Starting parallel processing...")
        mf = cl.mem_flags
        data = np.array(data, dtype=np.float32)
        data_buf = cl.Buffer(self.context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=data)
        output_buf = cl.Buffer(self.context, mf.WRITE_ONLY, data.nbytes)
        prg = cl.Program(self.context, '''
        __kernel void double_data(__global const float *data, __global float *output) {
            int i = get_global_id(0);
            output[i] = data[i] * 2;
        }
        ''').build()
        prg.double_data(self.queue, data.shape, None, data_buf, output_buf)
        result = np.empty_like(data)
        cl.enqueue_copy(self.queue, result, output_buf).wait()
        logging.info("Parallel processing completed.")
        return result