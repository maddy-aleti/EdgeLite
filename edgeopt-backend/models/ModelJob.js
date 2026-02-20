import mongoose from "mongoose";

const modelJobSchema = new mongoose.Schema(
  {
    originalFileName: String,
    optimizedFileName: String,
    originalSize: Number,
    optimizedSize: Number,
    sizeReduction: Number,
    status: {
      type: String,
      default: "processing",
    },
  },
  { timestamps: true }
);

export default mongoose.model("ModelJob", modelJobSchema);