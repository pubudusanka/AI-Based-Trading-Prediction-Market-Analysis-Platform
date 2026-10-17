"use client";

import React, { useState, useEffect } from "react";
import { NotificationItem, NotificationSettings } from "../types/market";
import { updateBackendNotificationSettings } from "../services/api";

interface NotificationCenterProps {
  notifications: NotificationItem[];
  onClearAll: () => void;
  onMarkRead: (id?: string) => void;
}

export function NotificationCenter({
  notifications,
  onClearAll,
  onMarkRead,
}: NotificationCenterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState<NotificationSettings>({
    notificationsEnabled: true,
    soundEnabled: true,
    minConfidenceThreshold: 0.65,
  });
  const [permissionStatus, setPermissionStatus] = useState<string>("default");

  useEffect(() => {
    if (typeof window !== "undefined" && "Notification" in window) {
      setPermissionStatus(Notification.permission);
    }
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const requestBrowserPermission = async () => {
    if (typeof window !== "undefined" && "Notification" in window) {
      try {
        const perm = await Notification.requestPermission();
        setPermissionStatus(perm);
      } catch {
        // ignore
      }
    }
  };

  const handleToggleNotifications = async () => {
    const next = !settings.notificationsEnabled;
    setSettings((prev) => ({ ...prev, notificationsEnabled: next }));
    await updateBackendNotificationSettings(next, settings.minConfidenceThreshold);
  };

  const handleToggleSound = () => {
    setSettings((prev) => ({ ...prev, soundEnabled: !prev.soundEnabled }));
  };

  const handleConfidenceChange = async (val: number) => {
    setSettings((prev) => ({ ...prev, minConfidenceThreshold: val }));
    await updateBackendNotificationSettings(settings.notificationsEnabled, val);
  };

  return (
    <div className="relative inline-block text-left">
      {/* Bell Icon Trigger */}
      <button
        id="notification-bell-btn"
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition flex items-center justify-center focus:outline-none"
        title="Alert Notifications"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>

        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-4 w-4">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500 text-[9px] font-bold text-slate-950 items-center justify-center">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          </span>
        )}
      </button>

      {/* Dropdown Drawer */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 max-w-[90vw] bg-slate-950 border border-slate-800 rounded-xl shadow-2xl z-50 overflow-hidden text-sm">
          {/* Header */}
          <div className="px-4 py-3 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-white">Notifications</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                {notifications.length}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowSettings(!showSettings)}
                className={`p-1 rounded text-xs transition ${
                  showSettings ? "text-cyan-400 bg-slate-800" : "text-slate-400 hover:text-white"
                }`}
                title="Alert Settings"
              >
                ⚙️
              </button>
              {notifications.length > 0 && (
                <button
                  onClick={onClearAll}
                  className="text-xs text-slate-400 hover:text-rose-400 transition"
                >
                  Clear all
                </button>
              )}
            </div>
          </div>

          {/* Settings Subpanel */}
          {showSettings && (
            <div className="p-3 bg-slate-900/60 border-b border-slate-800 text-xs space-y-2.5">
              <div className="font-semibold text-slate-300 uppercase tracking-wider text-[10px]">
                Alert Preferences (Strictly Optional)
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Receive Alerts</span>
                <button
                  onClick={handleToggleNotifications}
                  className={`w-10 h-5 flex items-center rounded-full p-0.5 transition ${
                    settings.notificationsEnabled ? "bg-emerald-500 justify-end" : "bg-slate-700 justify-start"
                  }`}
                >
                  <span className="w-4 h-4 rounded-full bg-white block shadow"></span>
                </button>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-400">Chirp Audio Alert</span>
                <button
                  onClick={handleToggleSound}
                  className={`w-10 h-5 flex items-center rounded-full p-0.5 transition ${
                    settings.soundEnabled ? "bg-cyan-500 justify-end" : "bg-slate-700 justify-start"
                  }`}
                >
                  <span className="w-4 h-4 rounded-full bg-white block shadow"></span>
                </button>
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-slate-400">
                  <span>Min Confidence Threshold</span>
                  <span className="font-mono text-cyan-400">
                    {(settings.minConfidenceThreshold * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="0.9"
                  step="0.05"
                  value={settings.minConfidenceThreshold}
                  onChange={(e) => handleConfidenceChange(parseFloat(e.target.value))}
                  className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                />
              </div>

              {permissionStatus !== "granted" && (
                <button
                  onClick={requestBrowserPermission}
                  className="w-full mt-1 py-1.5 px-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-medium text-[11px] transition text-center"
                >
                  Enable OS Native Push Alerts
                </button>
              )}
            </div>
          )}

          {/* Notification List */}
          <div className="max-h-80 overflow-y-auto divide-y divide-slate-900">
            {notifications.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                No active notifications.
              </div>
            ) : (
              notifications.map((item, idx) => {
                const isBuy = item.signal === "BUY" || item.type === "BUY_SIGNAL";
                const isSell = item.signal === "SELL" || item.type === "SELL_SIGNAL";
                const isRisk = item.type === "RISK_ALERT";

                return (
                  <div
                    key={item.id || idx}
                    onClick={() => onMarkRead(item.id)}
                    className={`p-3 transition cursor-pointer hover:bg-slate-900/70 ${
                      item.read ? "opacity-60" : "bg-slate-950"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-1.5">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            isBuy
                              ? "bg-emerald-400 shadow-sm shadow-emerald-500/50"
                              : isSell
                              ? "bg-rose-400 shadow-sm shadow-rose-500/50"
                              : isRisk
                              ? "bg-amber-400"
                              : "bg-cyan-400"
                          }`}
                        />
                        <span className="font-semibold text-slate-200 text-xs">
                          {item.title}
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {item.timestamp ? new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ""}
                      </span>
                    </div>

                    <p className="mt-1 text-xs text-slate-400 leading-relaxed font-sans">
                      {item.message}
                    </p>

                    {item.confidence && (
                      <div className="mt-2 flex items-center space-x-2 text-[10px]">
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                          Confidence: {(item.confidence * 100).toFixed(1)}%
                        </span>
                        {item.symbol && (
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
                            {item.symbol}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
