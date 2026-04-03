import express from "express";
import {requireAuth} from "../middleware/auth.js";

const router = express.Router();
router.use(requireAuth);

router.post("/agent/run", async (req, res) => {
  try {
    const data = req.body;

    // token already came from frontend
    const authHeader = req.headers["authorization"];

    const result = await fetch("http://localhost:8000/agent/run", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": authHeader, // 👈 forward exactly as received
      },
      body: JSON.stringify(data),
    });

    const response = await result.json();

    return res.json(response);
  } catch (e) {
    return res.status(500).json({ message: "server error" });
  }
});
export default router