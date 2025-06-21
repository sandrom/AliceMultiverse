#!/usr/bin/env python3
"""Fix only the indentation issues in alice_orchestrator.py"""

def fix_indentation():
    with open('alicemultiverse/interface/alice_orchestrator.py', 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Fix specific known indentation issues
        if i == 148 and 'return now.replace' in line:
            fixed_lines.append('            return now.replace(hour=0, minute=0, second=0, microsecond=0)\n')
        elif i == 150 and 'return now - timedelta(weeks=1)' in line:
            fixed_lines.append('            return now - timedelta(weeks=1)\n')
        elif i == 152 and 'return now - timedelta(days=30)' in line:
            fixed_lines.append('            return now - timedelta(days=30)\n')
        elif i == 154 and 'return now - timedelta(days=365)' in line:
            fixed_lines.append('            return now - timedelta(days=365)\n')
        elif i == 163 and 'amount = int' in line:
            fixed_lines.append('            amount = int(match.group(1))\n')
        elif i == 164 and 'unit = match.group' in line:
            fixed_lines.append('            unit = match.group(2)\n')
        elif i == 166 and 'return now - timedelta(days=amount)' in line:
            fixed_lines.append('                return now - timedelta(days=amount)\n')
        elif i == 168 and 'return now - timedelta(weeks=amount)' in line:
            fixed_lines.append('                return now - timedelta(weeks=amount)\n')
        elif i == 170 and 'return now - timedelta(days=amount * 30)' in line:
            fixed_lines.append('                return now - timedelta(days=amount * 30)\n')
        elif i == 172 and 'return now - timedelta(hours=amount)' in line:
            fixed_lines.append('                return now - timedelta(hours=amount)\n')
        elif i == 175 and '"january": 1,' in line:
            fixed_lines.append('            "january": 1,\n')
        elif i == 176 and '"february": 2,' in line:
            fixed_lines.append('            "february": 2,\n')
        elif i == 177 and '"march": 3,' in line:
            fixed_lines.append('            "march": 3,\n')
        elif i == 178 and '"april": 4,' in line:
            fixed_lines.append('            "april": 4,\n')
        elif i == 179 and '"may": 5,' in line:
            fixed_lines.append('            "may": 5,\n')
        elif i == 180 and '"june": 6,' in line:
            fixed_lines.append('            "june": 6,\n')
        elif i == 181 and '"july": 7,' in line:
            fixed_lines.append('            "july": 7,\n')
        elif i == 182 and '"august": 8,' in line:
            fixed_lines.append('            "august": 8,\n')
        elif i == 183 and '"september": 9,' in line:
            fixed_lines.append('            "september": 9,\n')
        elif i == 184 and '"october": 10,' in line:
            fixed_lines.append('            "october": 10,\n')
        elif i == 185 and '"november": 11,' in line:
            fixed_lines.append('            "november": 11,\n')
        elif i == 186 and '"december": 12,' in line:
            fixed_lines.append('            "december": 12,\n')
        elif i == 187 and '}' in line and i > 180:
            fixed_lines.append('        }\n')
        elif i == 190 and 'if month_name in text_lower:' in line:
            fixed_lines.append('            if month_name in text_lower:\n')
        elif i == 191 and '# Assume current year' in line:
            fixed_lines.append('                # Assume current year, or last year if month is in future\n')
        elif i == 192 and 'year = now.year' in line:
            fixed_lines.append('                year = now.year\n')
        elif i == 193 and 'if month_num > now.month:' in line:
            fixed_lines.append('                if month_num > now.month:\n')
        elif i == 194 and 'year -= 1' in line:
            fixed_lines.append('                    year -= 1\n')
        elif i == 195 and 'return datetime(year, month_num, 1)' in line:
            fixed_lines.append('                return datetime(year, month_num, 1)\n')
        elif i == 197 and 'return None' in line:
            fixed_lines.append('        return None\n')
        # Fix all the method body indentations
        elif i >= 141 and i <= 520:
            stripped = line.strip()
            if not stripped:
                fixed_lines.append('\n')
            elif line.startswith('    """') and i == 141:
                fixed_lines.append('        """Understand and execute any creative request.\n')
            elif line.startswith('    This is') and i > 140 and i < 150:
                fixed_lines.append('        This is the primary endpoint that interprets natural language\n')
            elif line.startswith('    and orchestrates') and i > 140:
                fixed_lines.append('        and orchestrates all necessary operations.\n')
            elif line.startswith('    Args:') and i > 140:
                fixed_lines.append('\n')
                fixed_lines.append('        Args:\n')
            elif line.startswith('    request:') and i > 140:
                fixed_lines.append('            request: Natural language request from AI assistant\n')
            elif line.startswith('    Returns:') and i > 140:
                fixed_lines.append('\n')
                fixed_lines.append('        Returns:\n')
            elif line.startswith('    Creative response') and i > 140:
                fixed_lines.append('            Creative response with results and context\n')
            elif line.startswith('    """') and i > 145 and i < 155:
                fixed_lines.append('        """\n')
            elif line.startswith('    try:') and i > 140:
                fixed_lines.append('        try:\n')
            elif line.startswith('    # ') and i > 140:
                fixed_lines.append('            ' + stripped + '\n')
            elif line.startswith('    intent = ') and i > 140:
                fixed_lines.append('            intent = self._determine_intent(request)\n')
            elif line.startswith('    temporal_ref = ') and i > 140:
                fixed_lines.append('            temporal_ref = self._parse_temporal_reference(request)\n')
            elif line.startswith('    creative_elements = ') and i > 140:
                fixed_lines.append('            creative_elements = self._extract_creative_elements(request)\n')
            elif line.startswith('    if intent == ') and i > 140:
                fixed_lines.append('            if intent == CreativeIntent.SEARCH:\n')
            elif line.startswith('    return await self._handle_search') and i > 140:
                fixed_lines.append('                return await self._handle_search(request, temporal_ref, creative_elements)\n')
            elif line.startswith('    elif intent == CreativeIntent.CREATE:') and i > 140:
                fixed_lines.append('            elif intent == CreativeIntent.CREATE:\n')
            elif line.startswith('    return await self._handle_creation') and i > 140:
                fixed_lines.append('                return await self._handle_creation(request, creative_elements)\n')
            elif line.startswith('    elif intent == CreativeIntent.ORGANIZE:') and i > 140:
                fixed_lines.append('            elif intent == CreativeIntent.ORGANIZE:\n')
            elif line.startswith('    return await self._handle_organization') and i > 140:
                fixed_lines.append('                return await self._handle_organization(request)\n')
            elif line.startswith('    elif intent == CreativeIntent.REMEMBER:') and i > 140:
                fixed_lines.append('            elif intent == CreativeIntent.REMEMBER:\n')
            elif line.startswith('    return await self._handle_memory_request') and i > 140:
                fixed_lines.append('                return await self._handle_memory_request(request)\n')
            elif line.startswith('    elif intent == CreativeIntent.EXPLORE:') and i > 140:
                fixed_lines.append('            elif intent == CreativeIntent.EXPLORE:\n')
            elif line.startswith('    return await self._handle_exploration') and i > 140:
                fixed_lines.append('                return await self._handle_exploration(request, creative_elements)\n')
            elif line.startswith('    else:') and i > 140 and i < 180:
                fixed_lines.append('            else:\n')
            elif line.startswith('    return await self._handle_general_request') and i > 140:
                fixed_lines.append('                return await self._handle_general_request(request)\n')
            elif line.startswith('    except Exception as e:') and i > 140:
                fixed_lines.append('\n')
                fixed_lines.append('        except Exception as e:\n')
            elif line.startswith('    logger.error') and i > 140:
                fixed_lines.append('            logger.error(f"Failed to understand request: {e}")\n')
            elif line.startswith('    return CreativeResponse(') and i > 140 and i < 200:
                fixed_lines.append('            return CreativeResponse(\n')
            elif line.startswith('    success=False,') and i > 140:
                fixed_lines.append('                success=False,\n')
            elif line.startswith('    message=') and i > 140:
                fixed_lines.append('                message=f"I encountered an error: {e!s}",\n')
            elif line.startswith('    suggestions=') and i > 140 and i < 200:
                fixed_lines.append('                suggestions=["Try rephrasing your request", "Be more specific about what you want"],\n')
            elif line.startswith('    )') and i > 140 and i < 185:
                fixed_lines.append('            )\n')
            elif line.startswith('    """') and '_determine_intent' in lines[i-1]:
                fixed_lines.append('        """Determine the creative intent from natural language."""\n')
            elif line.startswith('    request_lower = request.lower()') and i > 180:
                fixed_lines.append('        request_lower = request.lower()\n')
            elif line.startswith('    memory_keywords = ') and i > 180:
                fixed_lines.append('        memory_keywords = ["remember", "recall", "what did", "what have", "history", "past"]\n')
            elif line.startswith('    # Check for questions') and i > 180:
                fixed_lines.append('        # Check for questions about past searches/creations\n')
            elif line.startswith('    if any(keyword in request_lower for keyword in memory_keywords):') and i > 180:
                fixed_lines.append('        if any(keyword in request_lower for keyword in memory_keywords):\n')
            elif line.startswith('    return CreativeIntent.REMEMBER') and i > 180 and i < 200:
                fixed_lines.append('            return CreativeIntent.REMEMBER\n')
            elif line.startswith('    if ("what" in request_lower') and i > 180:
                fixed_lines.append('        if ("what" in request_lower and "have" in request_lower and\n')
            elif line.startswith('    any(word in request_lower') and i > 190:
                fixed_lines.append('                any(word in request_lower for word in ["searched", "created", "made", "looked"])):\n')
            elif line.startswith('    return CreativeIntent.REMEMBER') and i > 190 and i < 200:
                fixed_lines.append('            return CreativeIntent.REMEMBER\n')
            elif line.startswith('    search_keywords = ') and i > 180:
                fixed_lines.append('        search_keywords = ["find", "search", "look for", "where is", "show me", "get"]\n')
            elif line.startswith('    if any(keyword in request_lower for keyword in search_keywords):') and i > 180:
                fixed_lines.append('        if any(keyword in request_lower for keyword in search_keywords):\n')
            elif line.startswith('    return CreativeIntent.SEARCH') and i > 195 and i < 205:
                fixed_lines.append('            return CreativeIntent.SEARCH\n')
            elif line.startswith('    create_keywords = ') and i > 180:
                fixed_lines.append('        create_keywords = ["create", "generate", "make", "produce", "design"]\n')
            elif line.startswith('    if any(keyword in request_lower for keyword in create_keywords):') and i > 180:
                fixed_lines.append('        if any(keyword in request_lower for keyword in create_keywords):\n')
            elif line.startswith('    return CreativeIntent.CREATE') and i > 180:
                fixed_lines.append('            return CreativeIntent.CREATE\n')
            elif line.startswith('    organize_keywords = ') and i > 180:
                fixed_lines.append('        organize_keywords = ["organize", "sort", "arrange", "clean up", "structure"]\n')
            elif line.startswith('    if any(keyword in request_lower for keyword in organize_keywords):') and i > 180:
                fixed_lines.append('        if any(keyword in request_lower for keyword in organize_keywords):\n')
            elif line.startswith('    return CreativeIntent.ORGANIZE') and i > 180:
                fixed_lines.append('            return CreativeIntent.ORGANIZE\n')
            elif line.startswith('    explore_keywords = ') and i > 180:
                fixed_lines.append('        explore_keywords = ["explore", "variations", "similar", "related"]\n')
            elif line.startswith('    if any(keyword in request_lower for keyword in explore_keywords):') and i > 180:
                fixed_lines.append('        if any(keyword in request_lower for keyword in explore_keywords):\n')
            elif line.startswith('    return CreativeIntent.EXPLORE') and i > 180:
                fixed_lines.append('            return CreativeIntent.EXPLORE\n')
            elif line.startswith('    if "?" in request_lower:') and i > 210:
                fixed_lines.append('        if "?" in request_lower:\n')
            elif line.startswith('    return CreativeIntent.SEARCH') and i > 215:
                fixed_lines.append('            return CreativeIntent.SEARCH\n')
            elif line.startswith('    return CreativeIntent.SEARCH  # Default') and i > 180:
                fixed_lines.append('\n')
                fixed_lines.append('        return CreativeIntent.SEARCH  # Default\n')
            # Fix all remaining handler method bodies
            elif line.startswith('    """') and i > 220:
                fixed_lines.append('        ' + line.strip() + '\n')
            elif line.startswith('    try:') and i > 220:
                fixed_lines.append('        try:\n')
            elif line.startswith('    # ') and i > 220:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    search_params = {}') and i > 220:
                fixed_lines.append('            search_params = {}\n')
            elif line.startswith('    if ') and i > 220:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    search_params[') and i > 220:
                fixed_lines.append('                ' + line.strip() + '\n')
            elif line.startswith('    results = ') and i > 220:
                fixed_lines.append('                ' + line.strip() + '\n')
            elif line.startswith('    self._update_memory') and i > 220:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    suggestions = ') and i > 220:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    return CreativeResponse(') and i > 220:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    success=') and i > 220:
                fixed_lines.append('                ' + line.strip() + '\n')
            elif line.startswith('    message=') and i > 220:
                fixed_lines.append('                ' + line.strip() + '\n')
            elif line.startswith('    assets=') and i > 220:
                fixed_lines.append('                ' + line.strip() + '\n')
            elif line.startswith('    suggestions=') and i > 220:
                fixed_lines.append('                ' + line.strip() + '\n')
            elif line.startswith('    memory_updated=') and i > 220:
                fixed_lines.append('                ' + line.strip() + '\n')
            elif line.startswith('    )') and i > 260:
                fixed_lines.append('            )\n')
            elif line.startswith('    except Exception as e:') and i > 220:
                fixed_lines.append('\n')
                fixed_lines.append('        except Exception as e:\n')
            elif line.startswith('    logger.error') and i > 220:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    request_lower = ') and i > 330:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    if self.asset_repo:') and i > 380:
                fixed_lines.append('        ' + line.strip() + '\n')
            elif line.startswith('    keywords = ') and i > 380:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    assets = ') and i > 380:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    return [') and i > 380:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    return []') and i > 380:
                fixed_lines.append('        return []\n')
            elif line.startswith('    return {') and i > 400:
                fixed_lines.append('        return {\n')
            elif line.startswith('    "id":') and i > 400:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    "path":') and i > 400:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    "type":') and i > 400:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    "source":') and i > 400:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    "created":') and i > 400:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    "prompt":') and i > 400:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    "tags":') and i > 400:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    "quality":') and i > 400:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    }') and i > 410:
                fixed_lines.append('        }\n')
            elif line.startswith('    suggestions = []') and i > 420:
                fixed_lines.append('        suggestions = []\n')
            elif line.startswith('    if not results:') and i > 420:
                fixed_lines.append('\n')
                fixed_lines.append('        if not results:\n')
            elif line.startswith('    suggestions.append') and i > 420:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    elif len(results)') and i > 420:
                fixed_lines.append('        elif len(results) > 10:\n')
            elif line.startswith('    if not elements') and i > 420:
                fixed_lines.append('            if not elements["styles"]:\n')
            elif line.startswith('    return suggestions') and i > 420:
                fixed_lines.append('\n')
                fixed_lines.append('        return suggestions\n')
            elif line.startswith('    create_words = ') and i > 430:
                fixed_lines.append('        create_words = ["create", "generate", "make", "produce", "design"]\n')
            elif line.startswith('    prompt = request') and i > 430:
                fixed_lines.append('        prompt = request\n')
            elif line.startswith('    for word in create_words:') and i > 430:
                fixed_lines.append('        for word in create_words:\n')
            elif line.startswith('    # Replace all') and i > 430:
                fixed_lines.append('            # Replace all case variations\n')
            elif line.startswith('    prompt = prompt.replace') and i > 430:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    return prompt.strip()') and i > 430:
                fixed_lines.append('        return prompt.strip()\n')
            elif line.startswith('    style_additions = []') and i > 440:
                fixed_lines.append('        style_additions = []\n')
            elif line.startswith('    for key, value in styles.items():') and i > 440:
                fixed_lines.append('        for key, value in styles.items():\n')
            elif line.startswith('    if isinstance(value, str):') and i > 440:
                fixed_lines.append('            if isinstance(value, str):\n')
            elif line.startswith('    style_additions.append') and i > 440:
                fixed_lines.append('                style_additions.append(value)\n')
            elif line.startswith('    if style_additions:') and i > 440:
                fixed_lines.append('\n')
                fixed_lines.append('        if style_additions:\n')
            elif line.startswith('    return f"{prompt}') and i > 440:
                fixed_lines.append('            return f"{prompt}, {\', \'.join(style_additions)}"\n')
            elif line.startswith('    return prompt') and i > 440:
                fixed_lines.append('        return prompt\n')
            elif line.startswith('    return CreativeResponse(') and i > 460:
                fixed_lines.append('        return CreativeResponse(\n')
            elif line.startswith('    success=True,') and i > 460:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    message=') and i > 460:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    suggestions=') and i > 460:
                fixed_lines.append('            ' + line.strip() + '\n')
            elif line.startswith('    )') and i > 465:
                fixed_lines.append('        )\n')
            elif line.startswith('    if self.project_id and self.project_repo:') and i > 490:
                fixed_lines.append('        if self.project_id and self.project_repo:\n')
            elif line.startswith('    try:') and i > 490:
                fixed_lines.append('            try:\n')
            elif line.startswith('    # Update project context') and i > 490:
                fixed_lines.append('                # Update project context\n')
            elif line.startswith('    await publish_event(') and i > 490:
                fixed_lines.append('                await publish_event(\n')
            elif line.startswith('    "context.updated",') and i > 490:
                fixed_lines.append('                    "context.updated",\n')
            elif line.startswith('    {') and i > 490:
                fixed_lines.append('                    {\n')
            elif line.startswith('    "project_id":') and i > 490:
                fixed_lines.append('                        ' + line.strip() + '\n')
            elif line.startswith('    "context_type":') and i > 490:
                fixed_lines.append('                        ' + line.strip() + '\n')
            elif line.startswith('    "update_type":') and i > 490:
                fixed_lines.append('                        ' + line.strip() + '\n')
            elif line.startswith('    "context_key":') and i > 490:
                fixed_lines.append('                        ' + line.strip() + '\n')
            elif line.startswith('    "new_value":') and i > 490:
                fixed_lines.append('                        "new_value": {\n')
            elif line.startswith('    "recent_searches":') and i > 490:
                fixed_lines.append('                            ' + line.strip() + '\n')
            elif line.startswith('    "recent_creations":') and i > 490:
                fixed_lines.append('                            ' + line.strip() + '\n')
            elif line.startswith('    "active_styles":') and i > 490:
                fixed_lines.append('                            ' + line.strip() + '\n')
            elif line.startswith('    "patterns":') and i > 490:
                fixed_lines.append('                            ' + line.strip() + '\n')
            elif line.startswith('    },') and i > 505:
                fixed_lines.append('                        },\n')
            elif line.startswith('    }') and i > 510:
                fixed_lines.append('                    }\n')
            elif line.startswith('    )') and i > 512:
                fixed_lines.append('                )\n')
            elif line.startswith('    return True') and i > 510:
                fixed_lines.append('                return True\n')
            elif line.startswith('    except Exception as e:') and i > 510:
                fixed_lines.append('            except Exception as e:\n')
            elif line.startswith('    logger.error') and i > 510:
                fixed_lines.append('                logger.error(f"Failed to save context: {e}")\n')
            elif line.startswith('    return False') and i > 510:
                fixed_lines.append('        return False\n')
            elif line.startswith('    if self.session:') and i > 515:
                fixed_lines.append('        if self.session:\n')
            elif line.startswith('    self.session.close()') and i > 515:
                fixed_lines.append('            self.session.close()\n')
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Write back
    with open('alicemultiverse/interface/alice_orchestrator.py', 'w') as f:
        f.writelines(fixed_lines)
    
    print("Fixed indentation issues")

if __name__ == "__main__":
    fix_indentation()