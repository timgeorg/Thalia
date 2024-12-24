import torch

def check_cuda_availability():
    if torch.cuda.is_available():
        print("CUDA is available.")
        num_devices = torch.cuda.device_count()
        print(f"Number of CUDA devices: {num_devices}")
        for i in range(num_devices):
            print(f"Device {i}: {torch.cuda.get_device_name(i)}")
    else:
        print("CUDA is not available.")

    torch.zeros(1).cuda()  # Initialize CUDA to avoid delay on first run
    

if __name__ == "__main__":
    check_cuda_availability()