"use client";

import { useCoAgent, useCopilotAction } from "@copilotkit/react-core";
import { CopilotKitCSSProperties, CopilotSidebar } from "@copilotkit/react-ui";
import { useState } from "react";

export default function CopilotKitPage() {
  const [themeColor, setThemeColor] = useState("#6366f1");

  // 🪁 Frontend Actions: https://docs.copilotkit.ai/guides/frontend-actions
  useCopilotAction({
    name: "setThemeColor",
    parameters: [{
      name: "themeColor",
      description: "The theme color to set. Make sure to pick nice colors.",
      required: true, 
    }],
    handler({ themeColor }) {
      setThemeColor(themeColor);
    },
  });

  return (
    <main style={{ "--copilot-kit-primary-color": themeColor } as CopilotKitCSSProperties}>
      <YourMainContent themeColor={themeColor} />
      <CopilotSidebar
        clickOutsideToClose={false}
        defaultOpen={true}
        labels={{
          title: "Popup Assistant",
          initial: "👋 Hi, there! You're chatting with an agent. This agent comes with a few tools to get you started.\n\nFor example you can try:\n- **Frontend Tools**: \"Set the theme to orange\"\n- **Shared State**: \"Write a proverb about AI\"\n- **Generative UI**: \"Get the weather in SF\" (shows weather info in chat)\n- **Weather Cards**: \"Add a weather card for Beijing to the center of the page\" (adds persistent weather cards)\n\nAs you interact with the agent, you'll see the UI update in real-time to reflect the agent's **state**, **tool calls**, and **progress**."
        }}
      />
    </main>
  );
}

// State of the agent, make sure this aligns with your agent's state.
type AgentState = {
  proverbs: string[];
  weather_cards: Array<{ 
    location: string; 
    id: string; 
    weatherData?: {
      city: string;
      province: string;
      temperature: string;
      weather: string;
      humidity: string;
      wind_direction: string;
      wind_power: string;
      report_time: string;
    } | null;
  }>;
}

function YourMainContent({ themeColor }: { themeColor: string }) {
  // 🪁 Shared State: https://docs.copilotkit.ai/coagents/shared-state
  const { state, setState } = useCoAgent<AgentState>({
    name: "sample_agent",
    initialState: {
      proverbs: [
        "CopilotKit may be new, but its the best thing since sliced bread.",
      ],
      weather_cards: [],
    },
  })

  // 🪁 Frontend Actions: https://docs.copilotkit.ai/coagents/frontend-actions
  useCopilotAction({
    name: "addProverb",
    parameters: [{
      name: "proverb",
      description: "The proverb to add. Make it witty, short and concise.",
      required: true,
    }],
    handler: ({ proverb }) => {
      setState({
        ...state,
        proverbs: [...state.proverbs, proverb],
      });
    },
  });

  //🪁 Generative UI: https://docs.copilotkit.ai/coagents/generative-ui
  useCopilotAction({
    name: "get_weather",
    description: "Get the weather for a given location.",
    available: "disabled",
    parameters: [
      { name: "location", type: "string", required: true },
    ],
    render: ({ args }) => {
      return <WeatherCard location={args.location} themeColor={themeColor} />
    },
  });

  // 🎯 NEW: Add weather card to center of page (Frontend Action)
  useCopilotAction({
    name: "add_weather_card_to_center",
    description: "Add a weather card for a specific location to the center of the page.",
    parameters: [
      { name: "location", type: "string", required: true, description: "The location for the weather card" },
      { name: "weatherData", type: "object", required: false, description: "Weather data from backend (optional)" },
    ],
    handler: ({ location, weatherData }) => {
      console.log("Adding weather card for:", location, "with data:", weatherData);
      const newCard = {
        location,
        id: `weather-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        weatherData: weatherData ? {
          city: (weatherData as any).city || "",
          province: (weatherData as any).province || "",
          temperature: (weatherData as any).temperature || "",
          weather: (weatherData as any).weather || "",
          humidity: (weatherData as any).humidity || "",
          wind_direction: (weatherData as any).wind_direction || "",
          wind_power: (weatherData as any).wind_power || "",
          report_time: (weatherData as any).report_time || ""
        } : null,
      };
      const currentWeatherCards = Array.isArray(state.weather_cards) ? state.weather_cards : [];
      console.log("Current weather cards:", currentWeatherCards);
      const updatedWeatherCards = [...currentWeatherCards, newCard];
      console.log("Updated weather cards:", updatedWeatherCards);
      setState({
        ...state,
        weather_cards: updatedWeatherCards,
      });
    },
  });

  // 🎯 NEW: Remove weather card from center (Frontend Action)
  useCopilotAction({
    name: "remove_weather_card",
    description: "Remove a weather card from the center of the page.",
    parameters: [
      { name: "location", type: "string", required: true, description: "The location of the weather card to remove" },
    ],
    handler: ({ location }) => {
      const currentWeatherCards = Array.isArray(state.weather_cards) ? state.weather_cards : [];
      setState({
        ...state,
        weather_cards: currentWeatherCards.filter(card => card.location !== location),
      });
    },
  });

  return (
    <div
      style={{ backgroundColor: themeColor }}
      className="h-screen w-screen transition-colors duration-300 relative"
    >
      {/* 🎯 Weather Cards in Center */}
      {(() => {
        console.log("Rendering weather cards. State:", state.weather_cards);
        return Array.isArray(state.weather_cards) && state.weather_cards.length > 0 ? (
          <div className="absolute inset-0 flex items-center justify-center z-10">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-6xl w-full p-4">
              {state.weather_cards.map((card) => (
                <WeatherCard 
                  key={card.id}
                  location={card.location} 
                  themeColor={themeColor}
                  weatherData={card.weatherData}
                  onRemove={() => {
                    const currentWeatherCards = Array.isArray(state.weather_cards) ? state.weather_cards : [];
                    setState({
                      ...state,
                      weather_cards: currentWeatherCards.filter(c => c.id !== card.id),
                    });
                  }}
                />
            ))}
            </div>
          </div>
        ) : null;
      })()}

      {/* Main Content - Only show when no weather cards */}
      {(!Array.isArray(state.weather_cards) || state.weather_cards.length === 0) && (
        <div className="h-screen w-screen flex justify-center items-center flex-col">
          <div className="bg-white/20 backdrop-blur-md p-8 rounded-2xl shadow-xl max-w-2xl w-full">
            <h1 className="text-4xl font-bold text-white mb-2 text-center">Proverbs</h1>
            <p className="text-gray-200 text-center italic mb-6">This is a demonstrative page, but it could be anything you want! 🪁</p>
            <hr className="border-white/20 my-6" />
            <div className="flex flex-col gap-3">
              {state.proverbs?.map((proverb, index) => (
                <div 
                  key={index} 
                  className="bg-white/15 p-4 rounded-xl text-white relative group hover:bg-white/20 transition-all"
                >
                  <p className="pr-8">{proverb}</p>
                  <button 
                    onClick={() => setState({
                      ...state,
                      proverbs: state.proverbs?.filter((_, i) => i !== index),
                    })}
                    className="absolute right-3 top-3 opacity-0 group-hover:opacity-100 transition-opacity 
                      bg-red-500 hover:bg-red-600 text-white rounded-full h-6 w-6 flex items-center justify-center"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
            {state.proverbs?.length === 0 && <p className="text-center text-white/80 italic my-8">
              No proverbs yet. Ask the assistant to add some!
            </p>}
          </div>
        </div>
      )}
    </div>
  );
}

// Simple sun icon for the weather card
function SunIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-14 h-14 text-yellow-200">
      <circle cx="12" cy="12" r="5" />
      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" strokeWidth="2" stroke="currentColor" />
    </svg>
  );
}

// Weather card component where the location and themeColor are based on what the agent
// sets via tool calls.
function WeatherCard({ 
  location, 
  themeColor, 
  onRemove,
  weatherData
}: { 
  location?: string, 
  themeColor: string,
  onRemove?: () => void,
  weatherData?: {
    city: string;
    province: string;
    temperature: string;
    weather: string;
    humidity: string;
    wind_direction: string;
    wind_power: string;
    report_time: string;
  } | null
}) {
    return (
    <div
      style={{ backgroundColor: themeColor }}
      className="rounded-xl shadow-xl max-w-md w-full relative group"
    >
      {onRemove && (
        <button
          onClick={onRemove}
          className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-opacity 
            bg-red-500 hover:bg-red-600 text-white rounded-full h-6 w-6 flex items-center justify-center z-10"
        >
          ✕
        </button>
      )}
    <div className="bg-white/20 p-4 w-full">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-white capitalize">{weatherData?.city || location}</h3>
          <p className="text-white">{weatherData ? "实时天气" : "Current Weather"}</p>
        </div>
        <SunIcon />
      </div>
      
      <div className="mt-4 flex items-end justify-between">
        <div className="text-3xl font-bold text-white">
          {weatherData?.temperature ? `${weatherData.temperature}°C` : "70°"}
        </div>
        <div className="text-sm text-white">
          {weatherData?.weather || "Clear skies"}
        </div>
      </div>
      
      <div className="mt-4 pt-4 border-t border-white">
        <div className="grid grid-cols-3 gap-2 text-center">
          <div>
            <p className="text-white text-xs">湿度</p>
            <p className="text-white font-medium">{weatherData?.humidity ? `${weatherData.humidity}%` : "45%"}</p>
          </div>
          <div>
            <p className="text-white text-xs">风向</p>
            <p className="text-white font-medium">{weatherData?.wind_direction || "5 mph"}</p>
          </div>
          <div>
            <p className="text-white text-xs">风力</p>
            <p className="text-white font-medium">{weatherData?.wind_power || "72°"}</p>
          </div>
        </div>
      </div>
      
      {weatherData?.report_time && (
        <div className="mt-2 pt-2 border-t border-white/20">
          <p className="text-white text-xs text-center">
            更新时间: {weatherData.report_time}
          </p>
        </div>
      )}
    </div>
  </div>
  );
}

