import asyncio
from random import randint
from PIL import Image
import os
from time import sleep
import io
import torch
from diffusers import StableDiffusionPipeline

class ImageGenerator:
    def __init__(self):
        self.model_id = "dreamlike-art/dreamlike-photoreal-2.0"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Stable Diffusion model"""
        try:
            pipe = StableDiffusionPipeline.from_pretrained(
                self.model_id, 
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            ).to(self.device)
            print(f"Model loaded successfully on {self.device}")
            return pipe
        except Exception as e:
            print(f"Failed to load model: {e}")
            raise
    
    def open_images(self, prompt):
        """Open all generated images for the given prompt"""
        folder_path = os.path.join("Data")
        prompt = prompt.replace(" ", "_")  # Removed [:600]

        # Create the directory if it doesn't exist
        os.makedirs(folder_path, exist_ok=True)

        for i in range(1, 5):
            image_path = os.path.join(folder_path, f"{prompt}{i}.jpg")
            try:
                with Image.open(image_path) as img:
                    print(f"Opening image: {image_path}")
                    img.show()
                    sleep(1)  # Small delay between opening images
            except (IOError, FileNotFoundError) as e:
                print(f"Unable to open {image_path}: {e}")

    async def query(self, payload):
        """Generate an image based on the payload"""
        try:
            prompt = payload["inputs"]
            negative_prompt = payload.get("negative_prompt", 
                                        "blurry, low quality, distorted, bad anatomy")
            
            print(f"Generating image with prompt: {prompt}")
            
            image = await asyncio.to_thread(
                self.pipe,
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=25,
                guidance_scale=7.5,
                height=512,
                width=512
            )
            
            image_bytes_io = io.BytesIO()
            image.images[0].save(image_bytes_io, format="JPEG", quality=95)
            return image_bytes_io.getvalue()
        except Exception as e:
            print(f"[ERROR in query] {e}")
            return None

    async def generate_images(self, prompt: str):
        """Generate and save multiple images based on the prompt"""
        tasks = []
        
        # Create 4 variations
        for i in range(4):
            payload = {
                "inputs": prompt,
                "negative_prompt": "blurry, low quality, distorted, bad anatomy"
            }
            task = asyncio.create_task(self.query(payload))
            tasks.append(task)

        image_bytes_list = await asyncio.gather(*tasks)

        # Save all generated images
        for i, image_bytes in enumerate(image_bytes_list):
            if not image_bytes:
                continue
                
            try:
                # Verify the image is valid
                with Image.open(io.BytesIO(image_bytes)) as img:
                    img.verify()
                
                # Save to file
                safe_prompt = prompt.replace(" ", "_").replace(",", "")  # Removed [:100]
                output_path = os.path.join("Data", f"{safe_prompt}{i+1}.jpg")
                
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                    print(f"Saved image to: {output_path}")
                    
            except Exception as e:
                print(f"[ERROR] Failed to save image {i+1}: {e}")

    def GenerateImages(self, prompt: str):
        """Main function to handle image generation"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.generate_images(prompt))
        except Exception as e:
            print(f"[ERROR in GenerateImages] {e}")
        finally:
            loop.close()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Open the generated images
            self.open_images(prompt)

    def main(self):
        """Main loop to monitor for image generation requests"""
        data_file = os.path.join("Frontend", "Files", "ImageGeneration.data")
        
        while True:
            try:
                if not os.path.exists(data_file):
                    sleep(1)
                    continue
                    
                with open(data_file, "r") as f:
                    content = f.read().strip()
                    
                if not content:
                    sleep(1)
                    continue
                    
                try:
                    prompt, status = [x.strip() for x in content.split(",", 1)]
                except ValueError:
                    sleep(1)
                    continue
                    
                if status.lower() == "true":
                    print(f"Starting image generation for: {prompt}")
                    self.GenerateImages(prompt)
                    
                    # Reset the status
                    with open(data_file, "w") as f:
                        f.write("False,False")
                    
            except KeyboardInterrupt:
                print("\nExiting image generation...")
                break
            except Exception as e:
                print(f"[MAIN ERROR] {e}")
                sleep(1)

# For backward compatibility with the original script
def main():
    generator = ImageGenerator()
    generator.main()

if __name__ == "__main__":
    main()
