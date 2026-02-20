import express from "express";
import upload from "../middleware/uploadMiddleware.js";
import { optimizeModel } from "../controllers/optimizeController.js";

const router = express.Router();

router.post("/", upload.single("file"), optimizeModel);

export default router;