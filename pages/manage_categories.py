import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_utils import (
    load_categories, load_category_groups, 
    save_categories, save_category_groups,
    get_category_display_name
)

def show():
    st.header("📂 Manage Categories")
    
    # Create tabs for categories and groups
    tab1, tab2 = st.tabs(["🏷️ Categories", "📁 Category Groups"])
    
    with tab1:
        show_categories_tab()
    
    with tab2:
        show_groups_tab()

def show_categories_tab():
    # Load data
    categories_df = load_categories()
    groups_df = load_category_groups()
    
    # Add new category section
    with st.expander("➕ Add New Category", expanded=False):
        with st.form("add_category"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input("Category Name")
                new_emoji = st.text_input("Emoji (optional)", placeholder="📁")
            
            with col2:
                if len(groups_df) > 0:
                    new_group = st.selectbox(
                        "Group", 
                        options=groups_df['id'].tolist(),
                        format_func=lambda x: f"{groups_df[groups_df['id']==x].iloc[0].get('emoji', '📂')} {groups_df[groups_df['id']==x].iloc[0]['name']}"
                    )
                else:
                    st.warning("No groups available. Create a group first.")
                    new_group = None
                
                new_type = st.selectbox("Type", ["expense", "income", "transfer"])
            
            new_description = st.text_area("Description (optional)")
            
            if st.form_submit_button("Add Category"):
                if new_name and new_group is not None:
                    new_id = int(categories_df['id'].max() + 1) if len(categories_df) > 0 else 1
                    new_row = pd.DataFrame([{
                        'id': new_id,
                        'name': new_name,
                        'group_id': new_group,
                        'description': new_description,
                        'emoji': new_emoji,
                        'category_type': new_type,
                        'is_active': True,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }])
                    
                    categories_df = pd.concat([categories_df, new_row], ignore_index=True)
                    
                    if save_categories(categories_df):
                        st.success(f"Added category: {new_emoji} {new_name}")
                        st.rerun()
                else:
                    st.error("Please fill in at least the category name and select a group.")
    
    # Display categories by group
    if len(categories_df) > 0 and len(groups_df) > 0:
        for _, group in groups_df.iterrows():
            group_categories = categories_df[categories_df['group_id'] == group['id']]
            
            if len(group_categories) > 0:
                group_emoji = group.get('emoji', '📂') if pd.notna(group.get('emoji', '')) else '📂'
                st.markdown(f"### {group_emoji} {group['name']}")
                
                for _, cat in group_categories.iterrows():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    
                    with col1:
                        display_name = get_category_display_name(cat)
                        st.write(f"**{display_name}**")
                        if cat.get('description') and pd.notna(cat.get('description')):
                            st.caption(cat['description'])
                    
                    with col2:
                        st.caption(f"Type: {cat.get('category_type', 'expense')}")
                    
                    with col3:
                        if st.button("✏️", key=f"edit_cat_{cat['id']}", help="Edit category"):
                            st.session_state[f"edit_mode_{cat['id']}"] = True
                    
                    with col4:
                        if st.button("🗑️", key=f"delete_cat_{cat['id']}", help="Delete category"):
                            categories_df = categories_df[categories_df['id'] != cat['id']]
                            if save_categories(categories_df):
                                st.success("Category deleted!")
                                st.rerun()
                    
                    # Edit mode
                    if st.session_state.get(f"edit_mode_{cat['id']}", False):
                        with st.form(f"edit_form_{cat['id']}"):
                            edit_col1, edit_col2 = st.columns(2)
                            
                            with edit_col1:
                                edit_name = st.text_input("Name", value=cat['name'])
                                edit_emoji = st.text_input("Emoji", value=cat.get('emoji', ''))
                            
                            with edit_col2:
                                current_group_idx = 0
                                if cat['group_id'] in groups_df['id'].values:
                                    current_group_idx = groups_df[groups_df['id'] == cat['group_id']].index[0]
                                
                                edit_group = st.selectbox(
                                    "Group", 
                                    options=groups_df['id'].tolist(),
                                    index=current_group_idx,
                                    format_func=lambda x: f"{groups_df[groups_df['id']==x].iloc[0].get('emoji', '📂')} {groups_df[groups_df['id']==x].iloc[0]['name']}"
                                )
                                
                                type_options = ["expense", "income", "transfer"]
                                current_type_idx = 0
                                if cat.get('category_type') in type_options:
                                    current_type_idx = type_options.index(cat.get('category_type'))
                                
                                edit_type = st.selectbox("Type", type_options, index=current_type_idx)
                            
                            edit_description = st.text_area("Description", value=cat.get('description', ''))
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("💾 Save"):
                                    categories_df.loc[categories_df['id'] == cat['id'], 'name'] = edit_name
                                    categories_df.loc[categories_df['id'] == cat['id'], 'emoji'] = edit_emoji
                                    categories_df.loc[categories_df['id'] == cat['id'], 'group_id'] = edit_group
                                    categories_df.loc[categories_df['id'] == cat['id'], 'description'] = edit_description
                                    categories_df.loc[categories_df['id'] == cat['id'], 'category_type'] = edit_type
                                    categories_df.loc[categories_df['id'] == cat['id'], 'updated_at'] = datetime.now().isoformat()
                                    
                                    if save_categories(categories_df):
                                        st.success("Category updated!")
                                        if f"edit_mode_{cat['id']}" in st.session_state:
                                            del st.session_state[f"edit_mode_{cat['id']}"]
                                        st.rerun()
                            
                            with col_cancel:
                                if st.form_submit_button("❌ Cancel"):
                                    if f"edit_mode_{cat['id']}" in st.session_state:
                                        del st.session_state[f"edit_mode_{cat['id']}"]
                                    st.rerun()
                
                st.markdown("---")
    else:
        st.info("No categories found. Add a category group first, then add categories.")

def show_groups_tab():
    # Load data
    groups_df = load_category_groups()
    categories_df = load_categories()
    
    # Add new group section
    with st.expander("➕ Add New Group", expanded=False):
        with st.form("add_group"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_group_name = st.text_input("Group Name")
                new_group_emoji = st.text_input("Emoji (optional)", placeholder="📂")
            
            with col2:
                new_group_color = st.color_picker("Color", "#007bff")
            
            if st.form_submit_button("Add Group"):
                if new_group_name:
                    new_group_id = int(groups_df['id'].max() + 1) if len(groups_df) > 0 else 1
                    new_group_row = pd.DataFrame([{
                        'id': new_group_id,
                        'name': new_group_name,
                        'user_id': 13,  # Default user
                        'color': new_group_color,
                        'emoji': new_group_emoji,
                        'is_active': True,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }])
                    
                    groups_df = pd.concat([groups_df, new_group_row], ignore_index=True)
                    
                    if save_category_groups(groups_df):
                        st.success(f"Added group: {new_group_emoji} {new_group_name}")
                        st.rerun()
                else:
                    st.error("Please enter a group name.")
    
    # Display existing groups
    if len(groups_df) > 0:
        st.markdown("### Current Groups")
        
        for _, group in groups_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                group_emoji = group.get('emoji', '📂') if pd.notna(group.get('emoji', '')) else '📂'
                st.markdown(f"**{group_emoji} {group['name']}**")
                category_count = len(categories_df[categories_df['group_id'] == group['id']])
                st.caption(f"{category_count} categories")
            
            with col2:
                st.color_picker(
                    "Color", 
                    value=group.get('color', '#007bff'), 
                    key=f"color_display_{group['id']}", 
                    disabled=True,
                    label_visibility="collapsed"
                )
            
            with col3:
                if st.button("✏️", key=f"edit_group_{group['id']}", help="Edit group"):
                    st.session_state[f"edit_group_mode_{group['id']}"] = True
            
            with col4:
                if st.button("🗑️", key=f"delete_group_{group['id']}", help="Delete group"):
                    # Check if group has categories
                    group_categories = categories_df[categories_df['group_id'] == group['id']]
                    if len(group_categories) > 0:
                        st.error("Cannot delete group with categories. Move or delete categories first.")
                    else:
                        groups_df = groups_df[groups_df['id'] != group['id']]
                        if save_category_groups(groups_df):
                            st.success("Group deleted!")
                            st.rerun()
            
            # Edit mode for groups
            if st.session_state.get(f"edit_group_mode_{group['id']}", False):
                with st.form(f"edit_group_form_{group['id']}"):
                    edit_col1, edit_col2 = st.columns(2)
                    
                    with edit_col1:
                        edit_group_name = st.text_input("Name", value=group['name'])
                        edit_group_emoji = st.text_input("Emoji", value=group.get('emoji', ''))
                    
                    with edit_col2:
                        edit_group_color = st.color_picker("Color", value=group.get('color', '#007bff'))
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("💾 Save"):
                            groups_df.loc[groups_df['id'] == group['id'], 'name'] = edit_group_name
                            groups_df.loc[groups_df['id'] == group['id'], 'emoji'] = edit_group_emoji
                            groups_df.loc[groups_df['id'] == group['id'], 'color'] = edit_group_color
                            groups_df.loc[groups_df['id'] == group['id'], 'updated_at'] = datetime.now().isoformat()
                            
                            if save_category_groups(groups_df):
                                st.success("Group updated!")
                                if f"edit_group_mode_{group['id']}" in st.session_state:
                                    del st.session_state[f"edit_group_mode_{group['id']}"]
                                st.rerun()
                    
                    with col_cancel:
                        if st.form_submit_button("❌ Cancel"):
                            if f"edit_group_mode_{group['id']}" in st.session_state:
                                del st.session_state[f"edit_group_mode_{group['id']}"]
                            st.rerun()
            
            st.markdown("---")
    else:
        st.info("No groups found. Add a group to get started.")