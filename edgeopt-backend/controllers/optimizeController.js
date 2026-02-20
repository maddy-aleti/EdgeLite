import axios from "axios";
import fs from "fs";
import ModelJob from "../models/ModelJob.js";
import FormData from "form-data";

export const optimizeModel = async (req, res) => {
  try {
    const file = req.file;

    const originalSize = file.size / (1024 * 1024);

    // Save initial job
    const job = await ModelJob.create({
      originalFileName: file.filename,
      originalSize,
    });

    // Send file to Python service
    const formData = new FormData();
    formData.append("file", fs.createReadStream(file.path));

    const response = await axios.post(
      "http://localhost:8000/optimize",
      formData,
      {
        headers: formData.getHeaders(),
      }
    );

    const {
      optimizedFileName,
      optimizedSize,
      sizeReduction,
    } = response.data;

    job.optimizedFileName = optimizedFileName;
    job.optimizedSize = optimizedSize;
    job.sizeReduction = sizeReduction;
    job.status = "completed";

    await job.save();

    res.status(200).json(job);
  } catch (error) {
    console.error("Optimization Error:", error.message);
    console.error("Full Error:", error);
    res.status(500).json({ 
      error: error.message || "Optimization failed"
    });
  }
};