import React, { useEffect, useState } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';
import Link from '@tiptap/extension-link';
import TextAlign from '@tiptap/extension-text-align';
import Underline from '@tiptap/extension-underline';
import { 
  Bold, Italic, Underline as UnderlineIcon, Strikethrough, 
  List, ListOrdered, Quote, Minus, Image as ImageIcon, 
  Link as LinkIcon, AlignLeft, AlignCenter, AlignRight, AlignJustify,
  Heading1, Heading2, Heading3
} from 'lucide-react';

const MenuBar = ({ editor }) => {
  if (!editor) return null;

  return (
    <div className="flex flex-wrap items-center gap-1 p-2 bg-slate-900 border-b border-slate-700 rounded-t-xl">
      <button
        onClick={(e) => { e.preventDefault(); editor.chain().focus().toggleHeading({ level: 1 }).run(); }}
        className={`p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors ${editor.isActive('heading', { level: 1 }) ? 'bg-slate-700 text-white' : ''}`}
        title="Heading 1"
      >
        <Heading1 size={16} />
      </button>
      <button
        onClick={(e) => { e.preventDefault(); editor.chain().focus().toggleHeading({ level: 2 }).run(); }}
        className={`p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors ${editor.isActive('heading', { level: 2 }) ? 'bg-slate-700 text-white' : ''}`}
        title="Heading 2"
      >
        <Heading2 size={16} />
      </button>
      <button
        onClick={(e) => { e.preventDefault(); editor.chain().focus().toggleHeading({ level: 3 }).run(); }}
        className={`p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors ${editor.isActive('heading', { level: 3 }) ? 'bg-slate-700 text-white' : ''}`}
        title="Heading 3"
      >
        <Heading3 size={16} />
      </button>
      
      <div className="w-px h-6 bg-slate-700 mx-1" />

      <button
        onClick={(e) => { e.preventDefault(); editor.chain().focus().toggleBold().run(); }}
        className={`p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors ${editor.isActive('bold') ? 'bg-slate-700 text-white' : ''}`}
        title="Bold"
      >
        <Bold size={16} />
      </button>
      <button
        onClick={(e) => { e.preventDefault(); editor.chain().focus().toggleItalic().run(); }}
        className={`p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors ${editor.isActive('italic') ? 'bg-slate-700 text-white' : ''}`}
        title="Italic"
      >
        <Italic size={16} />
      </button>
      <button
        onClick={(e) => { e.preventDefault(); editor.chain().focus().toggleUnderline().run(); }}
        className={`p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors ${editor.isActive('underline') ? 'bg-slate-700 text-white' : ''}`}
        title="Underline"
      >
        <UnderlineIcon size={16} />
      </button>
      <button
        onClick={(e) => { e.preventDefault(); editor.chain().focus().toggleStrike().run(); }}
        className={`p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors ${editor.isActive('strike') ? 'bg-slate-700 text-white' : ''}`}
        title="Strikethrough"
      >
        <Strikethrough size={16} />
      </button>

      <div className="w-px h-6 bg-slate-700 mx-1" />

      <button
        onClick={(e) => { e.preventDefault(); editor.chain().focus().toggleBulletList().run(); }}
        className={`p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors ${editor.isActive('bulletList') ? 'bg-slate-700 text-white' : ''}`}
        title="Bullet List"
      >
        <List size={16} />
      </button>
      <button
        onClick={(e) => { e.preventDefault(); editor.chain().focus().toggleOrderedList().run(); }}
        className={`p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors ${editor.isActive('orderedList') ? 'bg-slate-700 text-white' : ''}`}
        title="Ordered List"
      >
        <ListOrdered size={16} />
      </button>
      <button
        onClick={(e) => { e.preventDefault(); editor.chain().focus().toggleBlockquote().run(); }}
        className={`p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors ${editor.isActive('blockquote') ? 'bg-slate-700 text-white' : ''}`}
        title="Blockquote"
      >
        <Quote size={16} />
      </button>
      <button
        onClick={(e) => { e.preventDefault(); editor.chain().focus().setHorizontalRule().run(); }}
        className="p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors"
        title="Horizontal Rule"
      >
        <Minus size={16} />
      </button>

      <div className="w-px h-6 bg-slate-700 mx-1" />

      <button
        onClick={(e) => { e.preventDefault(); editor.chain().focus().setTextAlign('left').run(); }}
        className={`p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors ${editor.isActive({ textAlign: 'left' }) ? 'bg-slate-700 text-white' : ''}`}
        title="Align Left"
      >
        <AlignLeft size={16} />
      </button>
      <button
        onClick={(e) => { e.preventDefault(); editor.chain().focus().setTextAlign('center').run(); }}
        className={`p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors ${editor.isActive({ textAlign: 'center' }) ? 'bg-slate-700 text-white' : ''}`}
        title="Align Center"
      >
        <AlignCenter size={16} />
      </button>
      <button
        onClick={(e) => { e.preventDefault(); editor.chain().focus().setTextAlign('right').run(); }}
        className={`p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors ${editor.isActive({ textAlign: 'right' }) ? 'bg-slate-700 text-white' : ''}`}
        title="Align Right"
      >
        <AlignRight size={16} />
      </button>

      <div className="w-px h-6 bg-slate-700 mx-1" />

      <button
        onClick={(e) => {
          e.preventDefault();
          const url = window.prompt('URL');
          if (url) {
            editor.chain().focus().setLink({ href: url }).run();
          }
        }}
        className={`p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors ${editor.isActive('link') ? 'bg-slate-700 text-white' : ''}`}
        title="Link"
      >
        <LinkIcon size={16} />
      </button>
      <button
        onClick={(e) => {
          e.preventDefault();
          const url = window.prompt('Image URL');
          if (url) {
            editor.chain().focus().setImage({ src: url }).run();
          }
        }}
        className="p-1.5 rounded hover:bg-slate-700 text-slate-300 transition-colors"
        title="Image"
      >
        <ImageIcon size={16} />
      </button>
    </div>
  );
};

const TiptapEditor = ({ value, onChange, placeholder }) => {
  const [isMounted, setIsMounted] = useState(false);

  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      Image.configure({
        inline: true,
      }),
      Link.configure({
        openOnClick: false,
      }),
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
    ],
    content: value,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
    editorProps: {
      attributes: {
        class: 'prose prose-invert max-w-none focus:outline-none min-h-[300px] p-4 bg-slate-950 text-slate-300 rounded-b-xl border border-slate-800 border-t-0',
      },
    },
  });

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (editor && value !== editor.getHTML()) {
      editor.commands.setContent(value);
    }
  }, [value, editor]);

  if (!isMounted) return <div className="min-h-[300px] bg-slate-950 rounded-xl border border-slate-800 animate-pulse" />;

  return (
    <div className="flex flex-col w-full rounded-xl shadow-sm">
      <MenuBar editor={editor} />
      <EditorContent editor={editor} />
    </div>
  );
};

export default TiptapEditor;
