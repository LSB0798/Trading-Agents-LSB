"""Constants and utilities related to analysts configuration."""

from src.agents import portfolio_manager
from src.agents.aswath_damodaran import aswath_damodaran_agent
from src.agents.ben_graham import ben_graham_agent
from src.agents.bill_ackman import bill_ackman_agent
from src.agents.cathie_wood import cathie_wood_agent
from src.agents.charlie_munger import charlie_munger_agent
from src.agents.fundamentals import fundamentals_analyst_agent
from src.agents.michael_burry import michael_burry_agent
from src.agents.phil_fisher import phil_fisher_agent
from src.agents.peter_lynch import peter_lynch_agent
from src.agents.sentiment import sentiment_analyst_agent
from src.agents.stanley_druckenmiller import stanley_druckenmiller_agent
from src.agents.technicals import technical_analyst_agent
from src.agents.valuation import valuation_analyst_agent
from src.agents.warren_buffett import warren_buffett_agent
from src.agents.rakesh_jhunjhunwala import rakesh_jhunjhunwala_agent
from src.agents.mohnish_pabrai import mohnish_pabrai_agent
from src.agents.nassim_taleb import nassim_taleb_agent
from src.agents.news_sentiment import news_sentiment_agent
from src.agents.growth_agent import growth_analyst_agent

# Define analyst configuration - single source of truth
ANALYST_CONFIG = {
    # Aswath Damodaran（阿斯瓦斯·达摩达兰）
    # 身份：估值大师，纽约大学金融学教授
    # 风格：专注于 内在价值 和财务指标，通过严谨的估值模型评估投资机会。
    "aswath_damodaran": { 
        "display_name": "Aswath Damodaran",
        "description": "The Dean of Valuation", 
        "investing_style": "Focuses on intrinsic value and financial metrics to assess investment opportunities through rigorous valuation analysis.",
        "agent_func": aswath_damodaran_agent,
        "type": "analyst",
        "order": 0,
    },
    # Ben Graham（本杰明·格雷厄姆）
    # 身份：价值投资之父，著有《聪明的投资者》《证券分析》
    # 风格：强调 安全边际，投资于被低估且基本面稳健的公司。
    "ben_graham": {
        "display_name": "Ben Graham",
        "description": "The Father of Value Investing",
        "investing_style": "Emphasizes a margin of safety and invests in undervalued companies with strong fundamentals through systematic value analysis.",
        "agent_func": ben_graham_agent,
        "type": "analyst",
        "order": 1,
    },
    # Bill Ackman（比尔·阿克曼）
    # 身份：激进投资者，Pershing Square 创始人
    # 风格：通过 战略激进主义 影响管理层，解锁价值，采取逆向投资。
    "bill_ackman": {
        "display_name": "Bill Ackman",
        "description": "The Activist Investor",
        "investing_style": "Seeks to influence management and unlock value through strategic activism and contrarian investment positions.",
        "agent_func": bill_ackman_agent,
        "type": "analyst",
        "order": 2,
    },
    # Cathie Wood（凯西·伍德）
    # 身份：成长投资女王，ARK Invest 创始人
    # 风格：聚焦 颠覆性创新 和成长型公司（如科技、生物技术）。
    "cathie_wood": {
        "display_name": "Cathie Wood",
        "description": "The Queen of Growth Investing",
        "investing_style": "Focuses on disruptive innovation and growth, investing in companies that are leading technological advancements and market disruption.",
        "agent_func": cathie_wood_agent,
        "type": "analyst",
        "order": 3,
    },
    # Charlie Munger（查理·芒格）
    # 身份：伯克希尔·哈撒韦副董事长，巴菲特的长期搭档
    # 风格：理性思考，注重 优质企业 和长期增长。
    "charlie_munger": {
        "display_name": "Charlie Munger",
        "description": "The Rational Thinker",
        "investing_style": "Advocates for value investing with a focus on quality businesses and long-term growth through rational decision-making.",
        "agent_func": charlie_munger_agent,
        "type": "analyst",
        "order": 4,
    },
    # Michael Burry（迈克尔·伯里）
    # 身份：《大空头》原型，Scion Asset Management 创始人
    # 风格：逆向投资，善于做空高估市场，投资被低估的资产。
    "michael_burry": {
        "display_name": "Michael Burry",
        "description": "The Big Short Contrarian",
        "investing_style": "Makes contrarian bets, often shorting overvalued markets and investing in undervalued assets through deep fundamental analysis.",
        "agent_func": michael_burry_agent,
        "type": "analyst",
        "order": 5,
    },
    # Mohnish Pabrai（莫尼什·帕伯莱）
    # 身份：帕伯莱投资基金创始人，价值投资者
    # 风格：Dhandho 投资法（低风险、高回报），强调安全边际和长期持有。
    "mohnish_pabrai": {
        "display_name": "Mohnish Pabrai",
        "description": "The Dhandho Investor",
        "investing_style": "Focuses on value investing and long-term growth through fundamental analysis and a margin of safety.",
        "agent_func": mohnish_pabrai_agent,
        "type": "analyst",
        "order": 6,
    },
    # Nassim Taleb（纳西姆·塔勒布）
    # 身份：《黑天鹅》《反脆弱》作者，风险分析师
    # 风格：关注 尾部风险、反脆弱性、不对称收益（有限下跌，无限上涨），采用杠铃策略。
    "nassim_taleb": {
        "display_name": "Nassim Taleb",
        "description": "The Black Swan Risk Analyst",
        "investing_style": "Focuses on tail risk, antifragility, and asymmetric payoffs. Uses barbell strategy, avoids fragile companies via negativa, and seeks convex positions with limited downside and unlimited upside.",
        "agent_func": nassim_taleb_agent,
        "type": "analyst",
        "order": 7,
    },
    # Peter Lynch（彼得·林奇）
    # 身份：富达麦哲伦基金前经理，传奇基金经理
    # 风格：“十倍股”投资者，主张“买你了解的东西”，投资于成长潜力强的公司。
    "peter_lynch": {
        "display_name": "Peter Lynch",
        "description": "The 10-Bagger Investor",
        "investing_style": "Invests in companies with understandable business models and strong growth potential using the 'buy what you know' strategy.",
        "agent_func": peter_lynch_agent,
        "type": "analyst",
        "order": 8,
    },
    # Phil Fisher（菲利普·费雪）
    # 身份：成长投资先驱，著有《普通股和不普通的利润》
    # 风格：闲聊法（scuttlebutt），注重管理层质量和创新能力，长期持有成长股。
    "phil_fisher": {
        "display_name": "Phil Fisher",
        "description": "The Scuttlebutt Investor",
        "investing_style": "Emphasizes investing in companies with strong management and innovative products, focusing on long-term growth through scuttlebutt research.",
        "agent_func": phil_fisher_agent,
        "type": "analyst",
        "order": 9,
    },
    # Rakesh Jhunjhunwala（拉凯什·金君瓦拉）
    # 身份：印度“大牛”，传奇个人投资者
    # 风格：利用 宏观经济洞察，投资于高成长行业，尤其是新兴市场。
    "rakesh_jhunjhunwala": {
        "display_name": "Rakesh Jhunjhunwala",
        "description": "The Big Bull Of India",
        "investing_style": "Leverages macroeconomic insights to invest in high-growth sectors, particularly within emerging markets and domestic opportunities.",
        "agent_func": rakesh_jhunjhunwala_agent,
        "type": "analyst",
        "order": 10,
    },
    # Stanley Druckenmiller（斯坦利·德鲁肯米勒）
    # 身份：宏观对冲基金经理，量子基金前操盘手
    # 风格：宏观投资，基于经济趋势布局货币、商品、利率等大类资产。
    "stanley_druckenmiller": {
        "display_name": "Stanley Druckenmiller",
        "description": "The Macro Investor",
        "investing_style": "Focuses on macroeconomic trends, making large bets on currencies, commodities, and interest rates through top-down analysis.",
        "agent_func": stanley_druckenmiller_agent,
        "type": "analyst",
        "order": 11,
    },
    # Warren Buffett（沃伦·巴菲特）
    # 身份：“奥马哈先知”，伯克希尔·哈撒韦掌门人
    # 风格：价值投资 + 护城河 分析，购买优秀公司并长期持有。
    "warren_buffett": {
        "display_name": "Warren Buffett",
        "description": "The Oracle of Omaha",
        "investing_style": "Seeks companies with strong fundamentals and competitive advantages through value investing and long-term ownership.",
        "agent_func": warren_buffett_agent,
        "type": "analyst",
        "order": 12,
    },
    # Technical Analyst（技术分析师）
    # 身份：通用角色，图表形态专家
    # 风格：通过 技术指标、价格行为、图表模式预测市场走势。
    "technical_analyst": {
        "display_name": "Technical Analyst",
        "description": "Chart Pattern Specialist",
        "investing_style": "Focuses on chart patterns and market trends to make investment decisions, often using technical indicators and price action analysis.",
        "agent_func": technical_analyst_agent,
        "type": "analyst",
        "order": 13,
    },
    # Fundamentals Analyst（基本面分析师）
    # 身份：财务报表专家
    # 风格：深入分析 财务报表 和经济指标，评估公司内在价值。
    "fundamentals_analyst": {
        "display_name": "Fundamentals Analyst",
        "description": "Financial Statement Specialist",
        "investing_style": "Delves into financial statements and economic indicators to assess the intrinsic value of companies through fundamental analysis.",
        "agent_func": fundamentals_analyst_agent,
        "type": "analyst",
        "order": 14,
    },
    # Growth Analyst（成长分析师）
    # 身份：成长股专家
    # 风格：分析 增长趋势 和估值，识别成长机会。
    "growth_analyst": {
        "display_name": "Growth Analyst",
        "description": "Growth Specialist",
        "investing_style": "Analyzes growth trends and valuation to identify growth opportunities through growth analysis.",
        "agent_func": growth_analyst_agent,
        "type": "analyst",
        "order": 15,
    },
    # News Sentiment Analyst（新闻情绪分析师）
    # 身份：新闻情绪专家
    # 风格：通过 新闻情感分析 预测市场动向，识别机会。
    "news_sentiment_analyst": {
        "display_name": "News Sentiment Analyst",
        "description": "News Sentiment Specialist",
        "investing_style": "Analyzes news sentiment to predict market movements and identify opportunities through news analysis.",
        "agent_func": news_sentiment_agent,
        "type": "analyst",
        "order": 16,
    },
    # Sentiment Analyst（市场情绪分析师）
    # 身份：市场情绪专家
    # 风格：衡量 投资者情绪 和行为，利用行为金融学预测市场。
    "sentiment_analyst": {
        "display_name": "Sentiment Analyst",
        "description": "Market Sentiment Specialist",
        "investing_style": "Gauges market sentiment and investor behavior to predict market movements and identify opportunities through behavioral analysis.",
        "agent_func": sentiment_analyst_agent,
        "type": "analyst",
        "order": 17,
    },
    # Valuation Analyst（估值分析师）
    # 身份：公司估值专家
    # 风格：运用多种估值模型（DCF、PE、PB等）确定公司的公允价值。
    "valuation_analyst": {
        "display_name": "Valuation Analyst",
        "description": "Company Valuation Specialist",
        "investing_style": "Specializes in determining the fair value of companies, using various valuation models and financial metrics for investment decisions.",
        "agent_func": valuation_analyst_agent,
        "type": "analyst",
        "order": 18,
    },
}

# Derive ANALYST_ORDER from ANALYST_CONFIG for backwards compatibility
ANALYST_ORDER = [(config["display_name"], key) for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])]


def get_analyst_nodes():
    """Get the mapping of analyst keys to their (node_name, agent_func) tuples."""
    return {key: (f"{key}_agent", config["agent_func"]) for key, config in ANALYST_CONFIG.items()}


def get_agents_list():
    """Get the list of agents for API responses."""
    return [
        {
            "key": key,
            "display_name": config["display_name"],
            "description": config["description"],
            "investing_style": config["investing_style"],
            "order": config["order"]
        }
        for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])
    ]
