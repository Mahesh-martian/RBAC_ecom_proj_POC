import {v2 as cloudinary} from "cloudinary"
import config from "../config"
import multer from "multer"
import path from "path"
import fs from "fs"
import { TCloudinaryResponse, TFile } from "../app/types/file"

cloudinary.config({
  cloud_name: config.cloudinary_name,
  api_key: config.cloudinary_api_key,
  api_secret: config.cloudinary_secret
})

const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const uploadPath = path.join(process.cwd(), "uploads");
    // Check if the folder exists; if not, create it
    if (!fs.existsSync(uploadPath)) {
      fs.mkdirSync(uploadPath, { recursive: true });
    }
    cb(null, uploadPath);
  },
  filename: function (req, file, cb) {
    cb(null, file.originalname);
  },
});


const upload = multer({storage: storage})

const uploadToCloudinary = async(file: TFile):Promise<TCloudinaryResponse | undefined> =>{
  return new Promise((resolve, reject ) => {
    cloudinary.uploader.upload(file.path, 
      (error: Error, result: TCloudinaryResponse) =>{
        fs.unlinkSync(file.path)
        if(error){
          reject(error)
        } else{
          resolve(result)
        }
      }
    )
  })
}

const uploadMultipleToCloudinary = async (files: TFile[]): Promise<TCloudinaryResponse[]> => {
  const uploadPromises = files.map((file) => uploadToCloudinary(file));

  
  const results = await Promise.all(uploadPromises);

  return results.filter((result): result is TCloudinaryResponse => result !== undefined);
};


export const fileUploader = {
  upload, uploadToCloudinary, uploadMultipleToCloudinary
}