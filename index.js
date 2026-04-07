// src/index.js — Entry point for Study Room Finder backend
// This file is kept minimal so GitHub Actions + Render can verify
// the deployment pipeline works end-to-end.

const express = require("express");
const app = express();
const PORT = process.env.PORT || 3001;

app.use(express.json());

// ─── HEALTH CHECK ─────────────────────────────────────────────
// GitHub Actions CD job polls this endpoint after deploy to confirm
// the server came up successfully on Render.
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    service: "study-room-finder-api",
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || "development",
  });
});

// ─── ROOMS ────────────────────────────────────────────────────
app.get("/api/rooms", (req, res) => {
  // TODO: Replace with real DB query using DATABASE_URL from Render env
  res.json({
    rooms: [
      { id: 1, name: "Library Room A", capacity: 6, available: true },
      { id: 2, name: "Library Room B", capacity: 4, available: false },
      { id: 3, name: "Science Hall 101", capacity: 10, available: true },
    ],
  });
});

// ─── BOOKINGS ─────────────────────────────────────────────────
app.post("/api/bookings", (req, res) => {
  const { roomId, userId, startTime, endTime } = req.body;
  if (!roomId || !userId || !startTime || !endTime) {
    return res.status(400).json({ error: "Missing required fields" });
  }
  // TODO: Save to PostgreSQL via DATABASE_URL
  res.status(201).json({
    message: "Booking confirmed",
    booking: { roomId, userId, startTime, endTime },
  });
});

app.listen(PORT, () => {
  console.log(`Study Room API running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});
