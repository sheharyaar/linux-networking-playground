// matvec.cu — the spine of gpu-programming-dossier.html: y = W·x
//
// W is d rows × n columns, row-major, FP32. x has n elements, y has d.
// Three kernels, each one fixing what the previous one got wrong:
//
//   matvec_naive  one thread per row.   Neighbouring threads read addresses
//                 n*4 bytes apart, so a warp's 32 loads hit 32 different
//                 sectors. Uncoalesced. (memory chapter, coalescing)
//   matvec_warp   one warp per row.     Lane i reads column i, i+32, ...
//                 Neighbouring lanes read neighbouring floats. Coalesced.
//                 A warp shuffle adds the 32 partial sums. (CUDA chapter)
//   matvec_warp4  as matvec_warp, but each lane loads a float4 (16 bytes)
//                 per instruction: ld.global.v4.f32 in PTX, LDG.E.128 in SASS.
//
// Build (laptop, Ada):   nvcc -O3 -lineinfo -arch=sm_89 matvec.cu -lcublas -o matvec
// Run:                   ./matvec            (defaults d=n=4096, 200 iterations)
//                        ./matvec 8192 8192 100
//
// It prints, per kernel: time per call, effective bandwidth (bytes moved /
// time), and the max error against cuBLAS sgemv. Bytes moved is counted as
// W + x + y once each — the minimum any correct kernel must move.

#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <vector>
#include <cuda_runtime.h>
#include <cublas_v2.h>

#define CHECK(call)                                                        \
	do {                                                               \
		cudaError_t e_ = (call);                                   \
		if (e_ != cudaSuccess) {                                   \
			fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, \
				cudaGetErrorString(e_));                   \
			exit(1);                                           \
		}                                                          \
	} while (0)

// One thread per row. Correct, simple, and slow.
__global__ void matvec_naive(const float *__restrict__ W,
			     const float *__restrict__ x,
			     float *__restrict__ y, int n, int d)
{
	int row = blockIdx.x * blockDim.x + threadIdx.x;
	if (row >= d)
		return;
	float sum = 0.0f;
	for (int j = 0; j < n; j++)
		sum += W[(size_t)row * n + j] * x[j];
	y[row] = sum;
}

// Add up one value per lane across the 32 lanes of a warp.
// After five steps, lane 0 holds the total.
__device__ __forceinline__ float warp_sum(float v)
{
	for (int offset = 16; offset > 0; offset /= 2)
		v += __shfl_down_sync(0xffffffff, v, offset);
	return v;
}

// One warp per row. blockDim.x must be a multiple of 32.
__global__ void matvec_warp(const float *__restrict__ W,
			    const float *__restrict__ x,
			    float *__restrict__ y, int n, int d)
{
	int warp = (blockIdx.x * blockDim.x + threadIdx.x) / 32;
	int lane = threadIdx.x % 32;
	if (warp >= d)
		return;
	const float *w = W + (size_t)warp * n;
	float sum = 0.0f;
	for (int j = lane; j < n; j += 32)
		sum += w[j] * x[j];
	sum = warp_sum(sum);
	if (lane == 0)
		y[warp] = sum;
}

// One warp per row, 16-byte loads. Requires n % 4 == 0.
__global__ void matvec_warp4(const float *__restrict__ W,
			     const float *__restrict__ x,
			     float *__restrict__ y, int n, int d)
{
	int warp = (blockIdx.x * blockDim.x + threadIdx.x) / 32;
	int lane = threadIdx.x % 32;
	if (warp >= d)
		return;
	const float4 *w4 = reinterpret_cast<const float4 *>(W + (size_t)warp * n);
	const float4 *x4 = reinterpret_cast<const float4 *>(x);
	float sum = 0.0f;
	for (int j = lane; j < n / 4; j += 32) {
		float4 a = w4[j], b = x4[j];
		sum += a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;
	}
	sum = warp_sum(sum);
	if (lane == 0)
		y[warp] = sum;
}

typedef void (*kernel_t)(const float *, const float *, float *, int, int);

static float time_kernel(kernel_t k, dim3 grid, dim3 block, const float *W,
			 const float *x, float *y, int n, int d, int iters)
{
	cudaEvent_t start, stop;
	CHECK(cudaEventCreate(&start));
	CHECK(cudaEventCreate(&stop));
	k<<<grid, block>>>(W, x, y, n, d); // warm-up: first launch pays for module load
	CHECK(cudaGetLastError());
	CHECK(cudaEventRecord(start));
	for (int i = 0; i < iters; i++)
		k<<<grid, block>>>(W, x, y, n, d);
	CHECK(cudaEventRecord(stop));
	CHECK(cudaEventSynchronize(stop));
	float ms;
	CHECK(cudaEventElapsedTime(&ms, start, stop));
	CHECK(cudaEventDestroy(start));
	CHECK(cudaEventDestroy(stop));
	return ms / iters;
}

static float max_err(const std::vector<float> &a, const std::vector<float> &b)
{
	float m = 0.0f;
	for (size_t i = 0; i < a.size(); i++)
		m = fmaxf(m, fabsf(a[i] - b[i]));
	return m;
}

int main(int argc, char **argv)
{
	int d = argc > 1 ? atoi(argv[1]) : 4096;
	int n = argc > 2 ? atoi(argv[2]) : 4096;
	int iters = argc > 3 ? atoi(argv[3]) : 200;

	cudaDeviceProp p;
	CHECK(cudaGetDeviceProperties(&p, 0));
	printf("device: %s, sm_%d%d, %d SMs, L2 %d KiB\n", p.name, p.major,
	       p.minor, p.multiProcessorCount, p.l2CacheSize / 1024);
	printf("d=%d n=%d, W is %.1f MiB\n", d, n,
	       (double)d * n * 4 / (1 << 20));

	std::vector<float> hW((size_t)d * n), hx(n), hy(d), ref(d);
	srand(1);
	for (auto &v : hW)
		v = rand() / (float)RAND_MAX - 0.5f;
	for (auto &v : hx)
		v = rand() / (float)RAND_MAX - 0.5f;

	float *W, *x, *y;
	CHECK(cudaMalloc(&W, hW.size() * sizeof(float)));
	CHECK(cudaMalloc(&x, n * sizeof(float)));
	CHECK(cudaMalloc(&y, d * sizeof(float)));
	CHECK(cudaMemcpy(W, hW.data(), hW.size() * sizeof(float),
			 cudaMemcpyHostToDevice));
	CHECK(cudaMemcpy(x, hx.data(), n * sizeof(float),
			 cudaMemcpyHostToDevice));

	// Reference: cuBLAS. It expects column-major, so our row-major W is
	// its transpose: ask for y = op(A)·x with op = transpose.
	cublasHandle_t h;
	cublasCreate(&h);
	float one = 1.0f, zero = 0.0f;
	cublasSgemv(h, CUBLAS_OP_T, n, d, &one, W, n, x, 1, &zero, y, 1);
	CHECK(cudaMemcpy(ref.data(), y, d * sizeof(float),
			 cudaMemcpyDeviceToHost));

	double bytes = ((double)d * n + n + d) * sizeof(float);
	int threads = 256, warps_per_block = threads / 32;
	struct {
		const char *name;
		kernel_t k;
		dim3 grid;
	} runs[] = {
		{"naive (thread/row)", matvec_naive, dim3((d + threads - 1) / threads)},
		{"warp  (warp/row)  ", matvec_warp, dim3((d + warps_per_block - 1) / warps_per_block)},
		{"warp4 (float4)    ", matvec_warp4, dim3((d + warps_per_block - 1) / warps_per_block)},
	};
	for (auto &r : runs) {
		CHECK(cudaMemset(y, 0, d * sizeof(float)));
		float ms = time_kernel(r.k, r.grid, dim3(threads), W, x, y, n, d, iters);
		CHECK(cudaMemcpy(hy.data(), y, d * sizeof(float),
				 cudaMemcpyDeviceToHost));
		printf("%s  grid=%5u  %8.3f us  %7.1f GB/s  max_err=%.2e\n",
		       r.name, r.grid.x, ms * 1e3, bytes / (ms * 1e-3) / 1e9,
		       max_err(hy, ref));
		// How many blocks of this kernel fit on one SM, and how many
		// rounds ("waves") of the whole GPU the grid needs.
		int per_sm;
		CHECK(cudaOccupancyMaxActiveBlocksPerMultiprocessor(&per_sm, r.k,
								    threads, 0));
		printf("    %d blocks/SM = %d warps/SM, %.2f waves\n", per_sm,
		       per_sm * warps_per_block,
		       (double)r.grid.x / (per_sm * p.multiProcessorCount));
	}

	// cuBLAS itself, for scale.
	cudaEvent_t s, e;
	cudaEventCreate(&s);
	cudaEventCreate(&e);
	cudaEventRecord(s);
	for (int i = 0; i < iters; i++)
		cublasSgemv(h, CUBLAS_OP_T, n, d, &one, W, n, x, 1, &zero, y, 1);
	cudaEventRecord(e);
	cudaEventSynchronize(e);
	float ms;
	cudaEventElapsedTime(&ms, s, e);
	ms /= iters;
	printf("cublasSgemv                    %8.3f us  %7.1f GB/s\n",
	       ms * 1e3, bytes / (ms * 1e-3) / 1e9);

	int preempt;
	CHECK(cudaDeviceGetAttribute(&preempt,
				     cudaDevAttrComputePreemptionSupported, 0));
	printf("compute preemption supported: %s\n", preempt ? "yes" : "no");

	cublasDestroy(h);
	cudaFree(W);
	cudaFree(x);
	cudaFree(y);
	return 0;
}
