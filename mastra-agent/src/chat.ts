import { customerServiceAgent } from "./mastra/agents/customer-service-agent.js";

const prompt = process.argv.slice(2).join(" ") || "查询订单 TEST-01-021 的物流";
const result = await customerServiceAgent.generate(prompt, { maxSteps: 5 });

console.log(result.text);
